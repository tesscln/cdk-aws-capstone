from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_iotsitewise as sitewise
)
from constructs import Construct

class CdkStackProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, asset_model_name: str,
                 asset_properties: list, assets: list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        print("Asset Model Properties Input:", asset_properties)

        if not isinstance(asset_properties, list) or not all(isinstance(prop, dict) for prop in asset_properties):
            raise ValueError("asset_properties must be a list of dictionaries")

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

        print("Assets Input:", assets)

        if not isinstance(assets, list) or not all(isinstance(asset, dict) for asset in assets):
            raise ValueError("assets must be a list of dictionaries")
        
        for asset in assets:
            if not isinstance(asset.get('properties'), list) or not all(isinstance(prop, dict) for prop in asset['properties']):
                raise ValueError("Each asset's properties must be a list of dictionaries")

        
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