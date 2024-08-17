import os
import boto3 # type: ignore
import json
import subprocess
import tempfile
import logging
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

s3_client = boto3.client('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_handler = logging.FileHandler('/tmp/conversion_log.txt')
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)

def upload_log_to_s3(bucket_name):
    try:
        s3_client.upload_file('/tmp/conversion_log.txt', bucket_name, 'conversion_log.txt')
    except Exception as e:
        print(f"Failed to upload log to S3: {str(e)}")

def convert_usd_to_gltf(input_usd, output_gltf):
    try:
        command = (
            f"blender --background --python-expr \"import bpy; "
            f"bpy.ops.wm.read_factory_settings(use_empty=True); "
            f"bpy.ops.wm.usd_import(filepath='{input_usd}'); "
            f"bpy.ops.export_scene.gltf(filepath='{output_gltf}', export_format='GLTF')\""
        )
        logger.info(f"Running conversion command: {command}")
        subprocess.run(command, shell=True, check=True)
        logger.info(f"Conversion successful: {output_gltf}")
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise

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

def process_file(bucket_name, usd_key):
    
    download_path = os.path.join(tempfile.gettempdir(), os.path.basename(usd_key))
    converted_file_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(usd_key)[0]}.gltf")
    
    try:
        logger.info(f"Downloading {usd_key} from bucket {bucket_name}")
        s3_client.download_file(bucket_name, usd_key, download_path)
        
        convert_usd_to_gltf(download_path, converted_file_path)
        
        upload_key = f"converted/{os.path.basename(converted_file_path)}"
        logger.info(f"Uploading converted file to {upload_key}")
        
        s3_client.upload_file(converted_file_path, bucket_name, upload_key)
        logger.info(f"File converted and uploaded to {upload_key}")
    
    except NoCredentialsError:
        logger.error("Credentials not available.")
    except ClientError as e:
        logger.error(f"Client error: {e}")
    except Exception as e:
        logger.error(f"Failed to process file: {str(e)}")
    finally:
        upload_log_to_s3(bucket_name)
        
    # Define where your metadata file is stored in S3
    bucket_name = os.environ['BUCKET_NAME']
    metadata_key = "upload_metadata.json"
    
    # Download the metadata file
    metadata_file_path = os.path.join(tempfile.gettempdir(), "upload_metadata.json")
    #s3_client.download_file(bucket_name, metadata_key, metadata_file_path)

    # Load metadata from the file
    with open(metadata_file_path, "r") as metadata_file:
        metadata_content = json.load(metadata_file)
    
    # Extract bucket name and file key
    usd_key = metadata_content['file_key']

bucket_name = os.environ['BUCKET_NAME']

metadata_file_path = os.path.join(tempfile.gettempdir(), "upload_metadata.json")
#s3_client.download_file(bucket_name, metadata_key, metadata_file_path)

# Load metadata from the file
with open(metadata_file_path, "r") as metadata_file:
    metadata_content = json.load(metadata_file)
    
# Extract bucket name and file key
usd_key = metadata_content['file_key']

if __name__ == "__main__":
    process_file(bucket_name, usd_key)
