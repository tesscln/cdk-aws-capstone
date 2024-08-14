import json
import os
import boto3 # type: ignore
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

def upload_file_to_s3(file_path, bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    try:
        file_key = os.path.basename(file_path)
        s3_client.upload_file(file_path, bucket_name, file_key)
        print(f"File {file_path} uploaded successfully to bucket '{bucket_name}' as '{file_key}'.")
        
        metadata_content = {
            "bucket_name": bucket_name,
            "file_key": file_key
        }
        
        metadata_file_path = "/tmp/upload_metadata.json"
        with open(metadata_file_path, "w") as metadata_file:
            json.dump(metadata_content, metadata_file)
        
        metadata_key = "upload_metadata.json"
        s3_client.upload_file(metadata_file_path, bucket_name, metadata_key)
        print(f"Metadata uploaded to '{bucket_name}' as ‘{metadata_key}'.")
        
        return bucket_name, file_key, metadata_key

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except NoCredentialsError:
        print("Credentials not available.")
    except ClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"Failed to upload file: {str(e)}")


if __name__ == "__main__":

    # Ask user for the file path
    file_path = input("Enter the file path to upload the 3D object (it needs to be in .usd format): ")

    # Ensure the file path is valid
    if not os.path.isfile(file_path):
        print("Invalid file path. Please ensure the file exists.")
        exit(1)

    # The bucket name should match the one created by the CDK
    bucket_name = input("Enter the bucket name (as shown in CDK deployment output): ")

    # The AWS region should match your CDK deployment region
    aws_region = input("Enter your AWS region (should match the CDK deployment region): ")

    # Upload the file
    uploaded_bucket_name, uploaded_file_key, uploaded_metadata_key = upload_file_to_s3(file_path, bucket_name, aws_region)



