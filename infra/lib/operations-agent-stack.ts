import * as path from 'node:path';
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as eventsources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3n from 'aws-cdk-lib/aws-s3-notifications';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as sqs from 'aws-cdk-lib/aws-sqs';

export class OperationsAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'OperationsVpc', {
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        { name: 'public', subnetType: ec2.SubnetType.PUBLIC },
        { name: 'private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
        { name: 'isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED }
      ]
    });

    const reportsBucket = new s3.Bucket(this, 'ReportsBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true
    });

    const jobsDlq = new sqs.Queue(this, 'JobsDlq', {
      retentionPeriod: cdk.Duration.days(14),
      encryption: sqs.QueueEncryption.SQS_MANAGED
    });
    const jobsQueue = new sqs.Queue(this, 'JobsQueue', {
      visibilityTimeout: cdk.Duration.minutes(5),
      deadLetterQueue: { queue: jobsDlq, maxReceiveCount: 3 },
      encryption: sqs.QueueEncryption.SQS_MANAGED
    });

    const auditTable = new dynamodb.Table(this, 'AuditTable', {
      partitionKey: { name: 'audit_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: { pointInTimeRecoveryEnabled: true },
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });
    auditTable.addGlobalSecondaryIndex({
      indexName: 'container-index',
      partitionKey: { name: 'container_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'created_at', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL
    });

    const alertsTopic = new sns.Topic(this, 'AlertsTopic', {
      displayName: 'Operations agent alerts'
    });

    const database = new rds.DatabaseInstance(this, 'OperationsDatabase', {
      engine: rds.DatabaseInstanceEngine.postgres({ version: rds.PostgresEngineVersion.VER_15 }),
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
      allocatedStorage: 20,
      maxAllocatedStorage: 50,
      credentials: rds.Credentials.fromGeneratedSecret('operations_agent'),
      databaseName: 'operations',
      publiclyAccessible: false,
      storageEncrypted: true,
      deletionProtection: false,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    const lambdaCode = lambda.Code.fromAsset(path.join(__dirname, '../../src'));
    const commonEnvironment = {
      APP_MODE: 'aws',
      BEDROCK_MODEL_ID: 'amazon.nova-lite-v1:0',
      REPORTS_BUCKET: reportsBucket.bucketName,
      JOBS_QUEUE_URL: jobsQueue.queueUrl,
      AUDIT_TABLE_NAME: auditTable.tableName,
      ALERTS_TOPIC_ARN: alertsTopic.topicArn,
      RDS_SECRET_ARN: database.secret?.secretArn ?? ''
    };

    const agentFunction = new lambda.Function(this, 'AgentFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'operations_agent.handlers.agent_api.agent_handler',
      code: lambdaCode,
      timeout: cdk.Duration.seconds(60),
      memorySize: 1024,
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      environment: commonEnvironment
    });
    const ingestionFunction = new lambda.Function(this, 'IngestionFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'operations_agent.handlers.ingestion.ingestion_handler',
      code: lambdaCode,
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      environment: commonEnvironment
    });
    ingestionFunction.addEventSource(new eventsources.SqsEventSource(jobsQueue, { batchSize: 5, reportBatchItemFailures: true }));

    reportsBucket.addEventNotification(s3.EventType.OBJECT_CREATED, new s3n.SqsDestination(jobsQueue), { suffix: '.json' });
    reportsBucket.grantRead(ingestionFunction);
    reportsBucket.grantRead(agentFunction);
    jobsQueue.grantConsumeMessages(ingestionFunction);
    auditTable.grantReadWriteData(agentFunction);
    auditTable.grantReadWriteData(ingestionFunction);
    alertsTopic.grantPublish(agentFunction);
    alertsTopic.grantPublish(ingestionFunction);
    database.secret?.grantRead(agentFunction);
    database.secret?.grantRead(ingestionFunction);
    agentFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel', 'bedrock:Converse'],
      resources: ['*']
    }));
    database.connections.allowDefaultPortFrom(agentFunction);
    database.connections.allowDefaultPortFrom(ingestionFunction);

    const api = new apigateway.RestApi(this, 'OperationsApi', {
      deployOptions: { stageName: 'v1' },
      defaultCorsPreflightOptions: { allowOrigins: apigateway.Cors.ALL_ORIGINS }
    });
    api.root.addResource('agent').addMethod('POST', new apigateway.LambdaIntegration(agentFunction));

    new cdk.CfnOutput(this, 'ApiUrl', { value: `${api.url}agent` });
    new cdk.CfnOutput(this, 'ReportsBucketName', { value: reportsBucket.bucketName });
    new cdk.CfnOutput(this, 'AuditTableName', { value: auditTable.tableName });
    new cdk.CfnOutput(this, 'JobsQueueUrl', { value: jobsQueue.queueUrl });
    new cdk.CfnOutput(this, 'AlertsTopicArn', { value: alertsTopic.topicArn });
  }
}
