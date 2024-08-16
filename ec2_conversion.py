import os
import boto3 # type: ignore
import json
import subprocess
import tempfile
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

s3_client = boto3.client('s3')

def convert_usd_to_gltf(input_usd, output_gltf):
    command = (
        f"blender --background --python-expr \"import bpy; "
        f"bpy.ops.wm.read_factory_settings(use_empty=True); "
        f"bpy.ops.wm.usd_import(filepath='{input_usd}'); "
        f"bpy.ops.export_scene.gltf(filepath='{output_gltf}', export_format='GLTF')\""
    )
    subprocess.run(command, shell=True, check=True)

def get_bucket_name_from_cfn(stack_name, export_name):
    """Retrieve the bucket name from CloudFormation outputs."""
    client = boto3.client('cloudformation')
    try:
        response = client.describe_stacks(StackName=stack_name)
        for output in response['Stacks'][0]['Outputs']:
            if output['ExportName'] == export_name:
                return output['OutputValue']
    except client.exceptions.ClientError as e:
        print(f"Error retrieving CloudFormation output: {e}")
        return None

def process_file():
    # Define where your metadata file is stored in S3
    bucket_name = os.environ['BUCKET_NAME']
    metadata_key = "upload_metadata.json"
    
    # Download the metadata file
    metadata_file_path = os.path.join(tempfile.gettempdir(), "upload_metadata.json")
    s3_client.download_file(bucket_name, metadata_key, metadata_file_path)

    # Load metadata from the file
    with open(metadata_file_path, "r") as metadata_file:
        metadata_content = json.load(metadata_file)
    
    # Extract bucket name and file key
    usd_key = metadata_content['file_key']
    
    download_path = os.path.join(tempfile.gettempdir(), os.path.basename(usd_key))
    converted_file_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(usd_key)[0]}.gltf")

    try:
        # Download the USD file from S3
        s3_client.download_file(bucket_name, usd_key, download_path)

        # Convert the USD file to GLTF using Blender
        convert_usd_to_gltf(download_path, converted_file_path)

        # Upload the converted file back to S3
        upload_key = f"converted/{os.path.basename(converted_file_path)}"
        s3_client.upload_file(converted_file_path, bucket_name, upload_key)

        print(f"File converted and uploaded to {upload_key}.")
    except NoCredentialsError:
        print("Credentials not available.")
    except ClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"Failed to process file: {str(e)}")

if __name__ == "__main__":
    process_file()
