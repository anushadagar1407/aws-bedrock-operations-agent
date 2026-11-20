import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { OperationsAgentStack } from '../lib/operations-agent-stack';

test('creates required event-driven resources', () => {
  const app = new cdk.App();
  const stack = new OperationsAgentStack(app, 'TestStack', {
    env: { account: '123456789012', region: 'us-east-1' }
  });
  const template = Template.fromStack(stack);
  template.resourceCountIs('AWS::S3::Bucket', 1);
  template.resourceCountIs('AWS::SQS::Queue', 2);
  template.resourceCountIs('AWS::DynamoDB::Table', 1);
  template.resourceCountIs('AWS::SNS::Topic', 1);
  template.resourceCountIs('AWS::RDS::DBInstance', 1);
});
