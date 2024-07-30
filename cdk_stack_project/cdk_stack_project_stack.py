from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_iotsitewise as sitewise,
    aws_iam as iam,
    CfnOutput,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions
)
from constructs import Construct
import json

class IotSensorsToDigitalTwinStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, asset_model_name: str,
                 asset_properties: list, assets: list, rules: list, mqtt_topics: list,
                  sns_topic_arns: dict, aws_region: str, aws_account_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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
        
        asset_ids = {}  # Store both the asset IDs and property IDs for Rule creation in IoT Core.
        property_ids = {}

        
        # Create an IoT SiteWise asset belonging to the created asset model

        for asset in assets:
            asset_properties = [
                sitewise.CfnAsset.AssetPropertyProperty(
                    logical_id=prop.get('logicalId', ""),
                    notification_state=prop.get('notification_state', "ENABLED"),
                    unit=prop.get('unit', "")
                ) for prop in asset['properties']
            ]
    
            asset_resource = sitewise.CfnAsset(self, f"{asset['name']}Asset",
                              asset_name=asset['name'],
                              asset_model_id=asset_model.ref,
                              asset_properties=asset_properties)
            
            asset_ids[asset['name']] = asset_resource.ref
            
            # Store property IDs
            property_ids[asset['name']] = {
                prop['name']: asset_model_properties[idx].logical_id
                for idx, prop in enumerate(asset['properties'])
            }
        
        # Create an IAM role for IoT rule actions

        iot_role = iam.Role(self, "IoTRole",
                            assumed_by=iam.ServicePrincipal("iot.amazonaws.com"),
                            managed_policies=[
                                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSIoTRuleActions")
                            ])
            
        print("Rules Input:", rules)

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
                property_id = property_ids[asset_name].get(property_name)
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
                                    asset_id=asset_id,
                                    property_id=property_id,
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
            
        # Output asset and property IDs to verify them

        for asset_name, asset_id in asset_ids.items():
            CfnOutput(self, f"{asset_name}AssetId", value=asset_id)
            for prop_name, prop_id in property_ids[asset_name].items():
                CfnOutput(self, f"{asset_name}{prop_name}PropertyId", value=prop_id)
        

#app = core.App()
#CdkStackProjectStack(app, "cdk-stack-project")
#app.synth()
