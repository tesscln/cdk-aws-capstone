#!/usr/bin/env python3
import os
import json
from aws_cdk import App

from cdk_stack_project.cdk_stack_project_stack import IotSensorsToDigitalTwinStack

app = App()


# Reading context variables:

asset_model_name = app.node.try_get_context("assetModelName")
asset_properties = app.node.try_get_context("assetProperties")
assets = app.node.try_get_context("assets")
rules = json.loads(app.node.try_get_context('rules'))
mqtt_topics = json.loads(app.node.try_get_context('mqttTopics'))
sns_topic_arns = json.loads(app.node.try_get_context('snsTopicArns'))
aws_region = app.node.try_get_context('awsRegion')
aws_account_id = app.node.try_get_context('awsAccountId')

# Ensure context variables are parsed correctly
if isinstance(asset_properties, str):
    try:
        asset_properties = json.loads(asset_properties)
    except json.JSONDecodeError as e:
        print(f"Error parsing assetProperties JSON: {e}")
        raise

if isinstance(assets, str):
    try:
        assets = json.loads(assets)
    except json.JSONDecodeError as e:
        print(f"Error parsing assets JSON: {e}")
        raise

print("Asset Model Name:", asset_model_name)
print("Asset Properties:", asset_properties)
print("Assets:", assets)

IotSensorsToDigitalTwinStack(app, "IotSensorsToDigitalTwinStack",
                     asset_model_name,
                     asset_properties,
                     assets,
                     rules, 
                     mqtt_topics,
                     sns_topic_arns,
                     aws_region,
                     aws_account_id
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
