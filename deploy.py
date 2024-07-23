import json
import os

# Defining a function collecting user input for asset model and properties

def get_asset_model_info():
    asset_model_name = input("Enter the asset model name: ")
    num_properties = int(input("Enter the number of properties: "))
    properties = []

    for _ in range(num_properties):
        name = input("Enter property name: ")
        data_type = input("Enter property data type (e.g., DOUBLE (float), STRING): ")
        unit = input("Enter property unit: ")
        properties.append({"name": name, "dataType": data_type, "unit": unit})
    
    return asset_model_name, properties

# Now, defining a function collecting user input for assets

def get_assets_info():
    num_assets = int(input("Enter the number of assets: "))
    assets = []

    for _ in range(num_assets):
        name = input("Enter asset name: ")
        num_properties = int(input("Enter the number of properties for asset {name}: "))
        properties = []

        for _ in range(num_properties):
            prop_name = input("Enter property name: ")
            data_type = input("Enter property data type (e.g., DOUBLE (float), STRING): ")
            unit = input("Enter property unit: ")
            properties.append({"name": prop_name, "dataType": data_type, "unit": unit})
        
        assets.append({"name": name, "properties": properties})
    
    return assets

# Running the functions to get user input

asset_model_name, asset_properties = get_asset_model_info()
assets = get_assets_info()

# Deploy the stack with the collected input

deploy_command = f'cdk deploy --context assetModelName="{asset_model_name}" ' \
                 f'--context \'assetProperties={json.dumps(asset_properties)}\' ' \
                 f'--context \'assets={json.dumps(assets)}\''

os.system(deploy_command)