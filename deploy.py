import json
import os
import uuid  # To generate a logicalId for the asset if the user does not provide one.

# Defining a function collecting user input for asset model and properties

def generate_logical_id():
    return str(uuid.uuid4())

def get_asset_model_info():
    valid_data_types = ["INTEGER", "STRING", "BOOLEAN", "DOUBLE"]
    asset_model_name = input("Enter the asset model name: ")
    num_properties = int(input("Enter the number of properties: "))
    properties = []

    for _ in range(num_properties):
        name = input("Enter property name: ")
        data_type = input(f"Enter property data type ({', '.join(valid_data_types)}): ")
        while data_type not in valid_data_types:
            print("Invalid data type. Please enter one of the following:", ", ".join(valid_data_types))
            data_type = input(f"Enter property data type ({', '.join(valid_data_types)}): ")
        unit = input("Enter property unit: ")
        logical_id = input("Enter property logical ID (or press enter to automatically generate a uuid): ")
        if not logical_id:
            logical_id = generate_logical_id()
        properties.append({"name": name, "dataType": data_type, "unit": unit, "logicalId": logical_id})

    return asset_model_name, properties

# Now, defining a function collecting user input for assets

def get_assets_info(properties):
    num_assets = int(input("Enter the number of assets: "))
    assets = []

    for _ in range(num_assets):
        name = input("Enter asset name: ")
        num_properties = int(input("Enter the number of properties for asset {name}: "))
        asset_properties = []

        for _ in range(num_properties):
            prop_name = input(f"Enter property name (choose from {', '.join([p['name'] for p in properties])}): ")
            while prop_name not in [p['name'] for p in properties]:
                print("Invalid property name. Please choose from the existing asset model properties.")
                prop_name = input(f"Enter property name (choose from {', '.join([p['name'] for p in properties])}): ")
            prop_data_type = next(p['dataType'] for p in properties if p['name'] == prop_name)
            prop_unit = next(p['unit'] for p in properties if p['name'] == prop_name)
            prop_logical_id = next(p['logicalId'] for p in properties if p['name'] == prop_name)
            asset_properties.append({"name": prop_name, "dataType": prop_data_type, "unit": prop_unit, "logicalId": prop_logical_id})
        
        assets.append({"name": name, "properties": asset_properties})
    
    return assets

if __name__ == "__main__":
    asset_model_name, asset_properties = get_asset_model_info()
    print("Asset Model Info:", asset_model_name, asset_properties)
    assets = get_assets_info(asset_properties)
    print("Assets Info:", assets)

    # Serialize to JSON
    asset_properties_json = json.dumps(asset_properties)
    assets_json = json.dumps(assets)

    # Print JSON outputs for inspection
    #print("Serialized assetProperties:", asset_properties_json)
    #print("Serialized assets:", assets_json)

    # Deploy the stack with the collected input
    deploy_command = (
        f'cdk deploy --context assetModelName="{asset_model_name}" ' 
        f'--context \'assetProperties={asset_properties_json}\' ' 
        f'--context \'assets={assets_json}\''
    )

    print("Deploy command:", deploy_command)

    os.system(deploy_command)