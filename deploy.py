import json
import os
import shlex
import boto3 # type: ignore
import sys
import uuid  # To generate a logicalId for the asset if the user does not provide one.
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

# Defining a function collecting user input for asset model and properties

def generate_logical_id():
    return str(uuid.uuid4())

def get_asset_model_info():
    valid_data_types = ["INTEGER", "STRING", "BOOLEAN", "DOUBLE"]
    asset_model_name = input("Enter the asset model name: ")
    while not asset_model_name:
        asset_model_name = input("Asset model name is required to create an asset model. Enter the asset model name: ")
    num_properties = int(input("Enter the number of properties: "))
    properties = []

    for _ in range(num_properties):
        name = input("Enter property name: ")
        while not name:
            name = input("Propety name is required to create a property. Enter the property name: ")
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

    while True:
        num_assets = input("Enter the number of assets: ")
        try:
            num_assets = int(num_assets)
            if num_assets > 0:
                break
            else:
                print("Number of assets must be greater than 0.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    assets = []

    for _ in range(num_assets):
        name = input("Enter asset name: ")
        num_properties = int(input(f"Enter the number of properties for asset {name}: "))
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

def create_bucket(bucket_name, region=None):
    s3_client = boto3.client('s3', region_name=region)
    try:
        if region is None or region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
        print(f"Bucket {bucket_name} created successfully in {region}.")
    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return False
    return True

def upload_file_to_s3(file_path, bucket_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_path, bucket_name, os.path.basename(file_path))
        print(f"File {file_path} uploaded successfully to {bucket_name}.")
    except Exception as e:
        print(f"Failed to upload file: {str(e)}")
        return False
    return True


# Function to collect MQTT topic subscription information
def get_mqtt_topics():
    num_topics = int(input("Enter the number of MQTT topics to subscribe to: "))
    topics = []

    for _ in range(num_topics):
        topic = input("Enter the MQTT topic name to subscribe to: ")
        topics.append(topic)
    
    return topics

# Ask the user for region and account ID
aws_region = input("Enter your AWS region: ")
aws_account_id = input("Enter your AWS account ID: ")

# Function to collect IoT Core rules information
def get_rules_info(assets):
    num_rules = int(input("Enter the number of rules (each rule will link data streams from sensors to a specific asset i.e. create one rule/asset): "))
    rules = []

    for asset in assets:
        rule_name = f"Rule{asset['name']}SynchronizingData"
        print("Available MQTT topics:", mqtt_topics)
        mqtt_topic = input(f"Enter the MQTT message topic name for asset '{asset['name']}' (choose from the above list): ")

        while mqtt_topic not in mqtt_topics:
            print(f"Invalid topic name. Please choose from the available topics: {', '.join(mqtt_topics)}")
            mqtt_topic = input(f"Enter the MQTT message topic name for asset '{asset['name']}' (choose from the above list): ")

        rule_actions = []

        for prop in asset['properties']:
            sensor_data = input(f"Enter the sensor data name for asset '{asset['name']}' property '{prop['name']}': ")
            rule_actions.append({
                "assetName": asset['name'],
                "propertyName": prop['name'],
                "sensorData": sensor_data,
                "mqttTopic": mqtt_topic
            })
        
        rules.append({"ruleName": rule_name, "actions": rule_actions})
    
    return rules

def main():
    asset_model_name, asset_properties = get_asset_model_info()
    file_path = input("Enter the file path to upload: ")
    bucket_name = f"{asset_model_name.lower().replace(' ', '-')}-usdfilebucket"

    if create_bucket(bucket_name, aws_region):
        if os.path.isfile(file_path):
            upload_file_to_s3(file_path, bucket_name)
        else:
            print("The file path provided does not exist.")

if __name__ == "__main__":
    asset_model_name, asset_properties = get_asset_model_info()
    print("Asset Model Info:", asset_model_name, asset_properties)
    assets = get_assets_info(asset_properties)
    print("Assets Info:", assets)
    mqtt_topics = get_mqtt_topics()
    print("MQTT Topics:", mqtt_topics)
    rules = get_rules_info(assets)
    print("Rules Info:", rules)

    # Serialize to JSON
    asset_properties_json = json.dumps(asset_properties)
    assets_json = json.dumps(assets)
    rules_json = json.dumps(rules)
    mqtt_topics_json = json.dumps(mqtt_topics)
    sns_topic_arns_json = json.dumps({
        topic: f"arn:aws:sns:{aws_region}:{aws_account_id}:{topic}" for topic in mqtt_topics
    })


    sns_topic_arns = {topic: f"arn:aws:sns:{aws_region}:{aws_account_id}:{topic}" for topic in mqtt_topics}

    # Print JSON outputs for inspection
    #print("Serialized assetProperties:", asset_properties_json)
    #print("Serialized assets:", assets_json)
    #print("Serialized rules:", rules_json)
    #print("Serialized mqttTopics:", mqtt_topics_json)
    #print("Serialized snsTopicArns:", sns_topic_arns_json)


    # Construct deploy command with proper quoting
    deploy_command = (
        f'cdk deploy '
        f'--context assetModelName={shlex.quote(asset_model_name)} '
        f'--context assetProperties={shlex.quote(asset_properties_json)} '
        f'--context assets={shlex.quote(assets_json)} '
        f'--context rules={shlex.quote(rules_json)} '
        f'--context mqttTopics={shlex.quote(mqtt_topics_json)} '
        f'--context snsTopicArns={shlex.quote(sns_topic_arns_json)} '
        f'--context awsRegion={shlex.quote(aws_region)} '
        f'--context awsAccountId={shlex.quote(aws_account_id)}'
    )

    print("Deploy command:", deploy_command)

    os.system(deploy_command)

    main()