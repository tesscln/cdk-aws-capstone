from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_iotsitewise as sitewise
)
from constructs import Construct

class CdkStackProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, asset_model_name: str,
                 asset_properties: list, assets: list, rules: list, mqtt_topics: list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Retrieve context variables
       # asset_model_name = self.node.try_get_context('assetModelName')
        #asset_properties = self.node.try_get_context('assetProperties')
        #assets = self.node.try_get_context('assets')

        print("Asset Model Name:", asset_model_name)
        print("Asset Properties:", asset_properties)
        print("Assets:", assets)

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

        
        # Create an IoT SiteWise asset belonging to the created asset model

        for asset in assets:
            asset_properties = [
                sitewise.CfnAsset.AssetPropertyProperty(
                    logical_id=prop.get('logicalId', ""),
                    notification_state=prop.get('notification_state', "ENABLED"),
                    unit=prop.get('unit', "")
                ) for prop in asset['properties']
            ]
    
            sitewise.CfnAsset(self, f"{asset['name']}Asset",
                              asset_name=asset['name'],
                              asset_model_id=asset_model.ref,
                              asset_properties=asset_properties)
            
        print("Rules Input:", rules)

        # Create IoT Core rules
        for rule in rules:
            sql_statement = f"SELECT {', '.join([action['sensorData'] for action in rule['actions']])}, timeInSeconds FROM '{rule['actions'][0]['mqttTopic']}'"
            actions = [
                iot.CfnTopicRule.ActionProperty(
                    iot_site_wise=iot.CfnTopicRule.IotSiteWiseActionProperty(
                        role_arn="<YOUR_ROLE_ARN>",
                        put_asset_property_value_entries=[
                            iot.CfnTopicRule.PutAssetPropertyValueEntryProperty(
                                entry_id=f"{action['assetName']}-{action['propertyName']}",
                                asset_id="<ASSET_ID>",
                                property_id="<PROPERTY_ID>",
                                property_values=[
                                    iot.CfnTopicRule.AssetPropertyValueProperty(
                                        value=iot.CfnTopicRule.AssetPropertyVariantProperty(
                                            double_value="$.sensordata"
                                        ),
                                        timestamp=iot.CfnTopicRule.AssetPropertyTimestampProperty(
                                            time_in_seconds="$.timeInSeconds"
                                        ),
                                        quality="GOOD"
                                    )
                                ]
                            ) for action in rule['actions']
                        ]
                    )
                )
            ]

            iot.CfnTopicRule(self, rule['ruleName'],
                             topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                                 sql=sql_statement,
                                 actions=actions,
                                 rule_disabled=False
                             ))
            
        # Create MQTT topic subscriptions

        for topic in mqtt_topics:
            iot.CfnTopicRule(self, f"{topic}Subscription",
                             topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                                 sql=f"SELECT * FROM '{topic}'",
                                 actions=[
                                     iot.CfnTopicRule.ActionProperty(
                                         sns=iot.CfnTopicRule.SnsActionProperty(
                                             target_arn="<YOUR_SNS_TOPIC_ARN>",
                                             role_arn="<YOUR_ROLE_ARN>"
                                         )
                                     )
                                 ],
                                 rule_disabled=False))

#app = core.App()
#CdkStackProjectStack(app, "cdk-stack-project")
#app.synth()
