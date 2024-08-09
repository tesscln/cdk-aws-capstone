import os
import boto3 # type: ignore
import tempfile
import subprocess
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    # Get the S3 bucket and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Define the local file paths
    download_path = os.path.join(tempfile.gettempdir(), os.path.basename(key))
    converted_file_path = os.path.join(tempfile.gettempdir(), f"{os.path.splitext(key)[0]}.gltf")

    try:
        # Download the USD file from S3
        s3_client.download_file(bucket_name, key, download_path)

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

def convert_usd_to_gltf(input_usd, output_gltf):
    # Use a subprocess call to run Blender CLI
    command = (
        f"blender --background --python-expr \"import bpy; "
        f"bpy.ops.wm.read_factory_settings(use_empty=True); "
        f"bpy.ops.wm.usd_import(filepath='{input_usd}'); "
        f"bpy.ops.export_scene.gltf(filepath='{output_gltf}', export_format='GLTF')\""
    )
    subprocess.run(command, shell=True, check=True)
