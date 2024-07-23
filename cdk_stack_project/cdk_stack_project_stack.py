from aws_cdk import (
    core,
    aws_iot as iot,
    aws_iotsitewise as sitewise
)
from constructs import Construct

class CdkStackProjectStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, asset_model_name: str,
                 asset_properties: list, assets: list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Defining an IoT SiteWise asset model:

        asset_model_properties = [
            {
                "name": prop['name'],
                "dataType": prop['dataType'],
                "unit": prop.get('unit', ""),
                "type": {
                    "measurement": {}
                }
            } for prop in asset_properties
        ]

        asset_model = sitewise.CfnAssetModel(
            self, "AssetModel",
            asset_model_name=asset_model_name,
            asset_model_properties=asset_model_properties
        )
        
        # Create an IoT SiteWise asset belonging to the created asset model

        for asset in assets:
            asset_properties = [
                {
                    "name": prop['name'],
                    "dataType": prop['dataType'],
                    "unit": prop.get('unit', ""),
                    "type": {
                        "measurement": {}
                    }
                } for prop in asset['properties']
            ]

            sitewise.CfnAsset(self, f"{asset['name']}Asset",
                              asset_name=asset['name'],
                              asset_model_id=asset_model.ref,
                              asset_properties=asset_properties)
            
#app = core.App()
#CdkStackProjectStack(app, "cdk-stack-project")
#app.synth()