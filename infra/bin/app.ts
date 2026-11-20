#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { OperationsAgentStack } from '../lib/operations-agent-stack';

const app = new cdk.App();
new OperationsAgentStack(app, 'OperationsAgentStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-east-1'
  }
});
