from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_iotsitewise as sitewise,
    aws_iam as iam,
    CfnOutput,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
    aws_iottwinmaker as iottwinmaker,
    aws_s3 as s3,
    RemovalPolicy,
    custom_resources as cr
)

from constructs import Construct
import json

class IotSensorsToDigitalTwinStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, asset_model_name: str,
                 asset_properties: list, assets: list, rules: list, mqtt_topics: list,
                  sns_topic_arns: dict, aws_region: str, aws_account_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 bucket
        bucket = s3.Bucket(self, "AssetModelBucket",
                           bucket_name=f"{asset_model_name.lower().replace(' ', '-')}-usdfilebucket",
                           removal_policy=RemovalPolicy.DESTROY)
        
        # Create an S3 bucket for IoT TwinMaker workspace
        twinmaker_bucket = s3.Bucket(self, "TwinMakerBucket",
                                     removal_policy=RemovalPolicy.DESTROY)

        # Output the bucket name to use it later
        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "TwinMakerBucketName", value=twinmaker_bucket.bucket_name)

        # Create an IAM role for TwinMaker with S3 access
        twinmaker_role = iam.Role(self, "TwinMakerRole",
                                  assumed_by=iam.ServicePrincipal("iottwinmaker.amazonaws.com"))

        # Grant necessary permissions to the TwinMaker role
        twinmaker_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3:ListBucket",
                "s3:GetObject",
                "s3:PutObject",
            ],
            resources=[
                twinmaker_bucket.bucket_arn,
                f"{twinmaker_bucket.bucket_arn}/*"
            ]
        ))

        twinmaker_bucket.grant_read_write(twinmaker_role)


        # Retrieve context variables
       # asset_model_name = self.node.try_get_context('assetModelName')
        #asset_properties = self.node.try_get_context('assetProperties')
        #assets = self.node.try_get_context('assets')

        print("Asset Model Name:", asset_model_name)
        print("Asset Model Properties input:", asset_properties)
        print("Assets:", assets)
        print("Rules Input:", rules)
        print("MQTT topics:", mqtt_topics)
        print("SNS Topic ARNs:", sns_topic_arns)
        

        if not isinstance(asset_properties, list) or not all(isinstance(prop, dict) for prop in asset_properties):
            raise ValueError("asset_properties must be a list of dictionaries")

        # Defining an IoT SiteWise asset model:

        asset_model_properties = [
            sitewise.CfnAssetModel.AssetModelPropertyProperty(
                name=prop['name'],
                data_type=prop['dataType'],  
                type=sitewise.CfnAssetModel.PropertyTypeProperty(
                    type_name="Measurement"  
                ),
                unit=prop['unit'],
                logical_id=prop.get('logicalId', "")
            ) for prop in asset_properties
        ]

        asset_model = sitewise.CfnAssetModel(
            self, "AssetModel",
            asset_model_name=asset_model_name,
            asset_model_properties=asset_model_properties
        )

        print("Assets Input:", assets)

        if not isinstance(assets, list) or not all(isinstance(asset, dict) for asset in assets):
            raise ValueError("assets must be a list of dictionaries")
        
        for asset in assets:
            if not isinstance(asset.get('properties'), list) or not all(isinstance(prop, dict) for prop in asset['properties']):
                raise ValueError("Each asset's properties must be a list of dictionaries")
        
        asset_ids = {}  # Store both the asset IDs and property aliases for Rule creation in IoT Core.
        property_aliases = {}
        

        # Create IoT SiteWise assets
        
        # Create an IoT SiteWise asset belonging to the created asset model

        for asset in assets:
            asset_properties = [
                sitewise.CfnAsset.AssetPropertyProperty(
                    logical_id=prop.get('logicalId', ""),
                    notification_state=prop.get('notification_state', "ENABLED"),
                    unit=prop.get('unit', ""),
                    alias=f"/{asset['name']}/{prop['name']}"
                ) for prop in asset['properties']
            ]
    
            asset_resource = sitewise.CfnAsset(self, f"{asset['name']}Asset",
                              asset_name=asset['name'],
                              asset_model_id=asset_model.ref,
                              asset_properties=asset_properties)
            
            asset_ids[asset['name']] = asset_resource.ref

            # Store the property aliases 

            property_aliases[asset['name']] = {
                prop['name']: f"/{asset['name']}/{prop['name']}"
                for prop in asset['properties']
            }
        
        # Create an IAM role for IoT rule actions

        iot_role = iam.Role(self, "IoTRole",
                            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"))
        
        # Attach managed policies to the role
        iot_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSIoTRuleActions"))

        # Add trust relationship for TwinMaker if needed
        # iot_role.add_to_principal_policy(
        #     iam.PolicyStatement(
        #         effect=iam.Effect.ALLOW,
        #         actions=["sts:AssumeRole"],
        #         principals=[iam.ServicePrincipal("iottwinmaker.amazonaws.com")]
        #     )
        # )

        # Attach custom inline policy
        iot_role.attach_inline_policy(
            iam.Policy(self, "CustomIoTPolicy",
                       statements=[
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "s3:Get*",
                                   "s3:List*",
                                   "s3:Describe*",
                                   "s3-object-lambda:Get*",
                                   "s3-object-lambda:List*",
                                   "s3:PutObject"
                               ],
                               resources=[bucket.bucket_arn, f"{bucket.bucket_arn}/*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "logs:CreateLogGroup",
                                   "logs:CreateLogStream",
                                   "logs:PutLogEvents",
                                   "logs:PutMetricFilter",
                                   "logs:PutRetentionPolicy",
                                   "logs:GetLogEvents",
                                   "logs:DeleteLogStream"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "dynamodb:PutItem",
                                   "kinesis:PutRecord",
                                   "iot:Publish",
                                   "s3:PutObject",
                                   "sns:Publish",
                                   "sqs:SendMessage*",
                                   "cloudwatch:SetAlarmState",
                                   "cloudwatch:PutMetricData",
                                   "es:ESHttpPut",
                                   "firehose:PutRecord"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "iotsitewise:*"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "iot:AddThingToThingGroup",
                                   "iot:AttachPolicy",
                                   "iot:AttachPrincipalPolicy",
                                   "iot:AttachThingPrincipal",
                                   "iot:CreateCertificateFromCsr",
                                   "iot:CreatePolicy",
                                   "iot:CreateThing",
                                   "iot:DescribeCertificate",
                                   "iot:DescribeThing",
                                   "iot:DescribeThingGroup",
                                   "iot:DescribeThingType",
                                   "iot:DetachPolicy",
                                   "iot:DetachThingPrincipal",
                                   "iot:GetPolicy",
                                   "iot:ListAttachedPolicies",
                                   "iot:ListPolicyPrincipals",
                                   "iot:ListPrincipalPolicies",
                                   "iot:ListPrincipalThings",
                                   "iot:ListTargetsForPolicy",
                                   "iot:ListThingGroupsForThing",
                                   "iot:ListThingPrincipals",
                                   "iot:RegisterCertificate",
                                   "iot:RegisterThing",
                                   "iot:RemoveThingFromThingGroup",
                                   "iot:UpdateCertificate",
                                   "iot:UpdateThing",
                                   "iot:UpdateThingGroupsForThing",
                                   "iot:AddThingToBillingGroup",
                                   "iot:DescribeBillingGroup",
                                   "iot:RemoveThingFromBillingGroup"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "iotsitewise:BatchPutAssetPropertyValue",
                                   "iotanalytics:BatchPutMessage",
                                   "iotevents:BatchPutMessage"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=["iot:Publish"],
                               resources=["arn:aws:iot:us-east-1:339713069268:topic/wheel-speed-error-action"]
                           ),
                           # Permissions for IoT TwinMaker
                           iam.PolicyStatement(
                               effect=iam.Effect.ALLOW,
                               actions=[
                                   "iottwinmaker:CreateWorkspace",
                                   "iottwinmaker:DeleteWorkspace",
                                   "iottwinmaker:GetWorkspace",
                                   "iottwinmaker:ListWorkspaces",
                                   "iottwinmaker:UpdateWorkspace",
                                   "iottwinmaker:TagResource",
                                   "iottwinmaker:UntagResource",
                                   "iottwinmaker:ListTagsForResource"
                               ],
                               resources=["*"]
                           )
                       ])
        )


        # Grant the IoT role read/write permissions to the bucket
        bucket.grant_read_write(iot_role)

        twinmaker_bucket.grant_read_write(iot_role)
            
        print("Rules Input:", rules)

         # Create SNS topics and subscriptions

        for topic in mqtt_topics:
            if topic not in sns_topic_arns:
                sns_topic = sns.Topic(self, f"{topic}Topic")
                sns_topic_arns[topic] = sns_topic.topic_arn

        # Create MQTT topic subscriptions

        #existing_sns_topic_arn = f"arn:aws:sns:{aws_region}:{aws_account_id}:{sns_topic_name}"

        for topic in mqtt_topics:
            iot.CfnTopicRule(self, f"{topic}Subscription",
                             topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                                 sql=f"SELECT * FROM '{topic}'",
                                 actions=[
                                     iot.CfnTopicRule.ActionProperty(
                                         sns=iot.CfnTopicRule.SnsActionProperty(
                                             target_arn=sns_topic_arns[topic],
                                             role_arn=iot_role.role_arn
                                         )
                                     )
                                 ],
                                 rule_disabled=False))

        # Create IoT Core rules
        for rule in rules:
            asset_name = rule['actions'][0]['assetName']
            mqtt_topic = rule['actions'][0]['mqttTopic']
            sql_statement = f"SELECT {', '.join([action['sensorData'] for action in rule['actions']])}, timeInSeconds FROM '{mqtt_topic}'"
           # actions = [
                #iot.CfnTopicRule.ActionProperty(
                   # iot_site_wise=iot.CfnTopicRule.IotSiteWiseActionProperty(
                        #role_arn=iot_role.role_arn,
                       # put_asset_property_value_entries=[
                            #iot.CfnTopicRule.PutAssetPropertyValueEntryProperty(
                              #               value=iot.CfnTopicRule.AssetPropertyVariantProperty(
                        #                    double_value="$.sensordata"
                       #                 ),
                      #                  timestamp=iot.CfnTopicRule.AssetPropertyTimestampProperty(
                     #                       time_in_seconds="$.timeInSeconds"
                    #                    ),
                   #                     quality="GOOD"
                  #                  )
                 #               ]
                #            ) for action in rule['actions']
               #         ]
              #      )
             #   )
            #]

            # Create actions for each property
            actions = []
            for action in rule['actions']:
                property_name = action['propertyName']
                sensor_data = action['sensorData']
                property_alias = property_aliases[asset_name].get(property_name)
                asset_id = asset_ids[asset_name]
                
                # Determine data type
                data_type = next(prop.data_type for prop in asset_model_properties if prop.name == property_name)
                if data_type == "DOUBLE":
                    value = f"${{{sensor_data}}}"
                else:
                    value = f"${{{sensor_data}}}"
                
                # Create action
                actions.append(
                    iot.CfnTopicRule.ActionProperty(
                        iot_site_wise=iot.CfnTopicRule.IotSiteWiseActionProperty(
                            role_arn=iot_role.role_arn,
                            put_asset_property_value_entries=[
                                iot.CfnTopicRule.PutAssetPropertyValueEntryProperty(
                                    entry_id=f"{asset_name}-{property_name}",
                                    property_alias=property_alias,
                                    property_values=[
                                        iot.CfnTopicRule.AssetPropertyValueProperty(
                                            value=iot.CfnTopicRule.AssetPropertyVariantProperty(
                                                double_value=value if data_type == "DOUBLE" else None,
                                                integer_value=value if data_type == "INTEGER" else None
                                            ),
                                            timestamp=iot.CfnTopicRule.AssetPropertyTimestampProperty(
                                                time_in_seconds="${floor(timestamp() / 1E3)}"
                                            ),
                                            quality="GOOD"
                                        )
                                    ]
                                )
                            ]
                        )
                    )
                )

            iot.CfnTopicRule(self, rule['ruleName'],
                             topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                                 sql=sql_statement,
                                 actions=actions,
                                 rule_disabled=False
                             ))
            
        # Create a workspace in IoT TwinMaker

        workspace_name = f"{asset_model_name}-workspace"
        workspace = iottwinmaker.CfnWorkspace(self, "Workspace",
                                              role=twinmaker_role.role_arn,
                                              s3_location=twinmaker_bucket.bucket_arn,
                                               workspace_id=workspace_name)
        
            
        # Output asset and property IDs to verify them

        for asset_name, asset_id in asset_ids.items():
            CfnOutput(self, f"{asset_name}AssetId", value=asset_id)
            for prop_name, prop_alias in property_aliases[asset_name].items():
                CfnOutput(self, f"{asset_name}{prop_name}PropertyAlias", value=prop_alias)

        CfnOutput(self, "WorkspaceId", value=workspace.workspace_id)

#app = core.App()
#CdkStackProjectStack(app, "cdk-stack-project")
#app.synth()
