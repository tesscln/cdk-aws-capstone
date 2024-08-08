import os
import boto3 # type: ignore
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

def upload_file_to_s3(file_path, bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    try:
        s3_client.upload_file(file_path, bucket_name, os.path.basename(file_path))
        print(f"File {file_path} uploaded successfully to bucket '{bucket_name}'.")
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
    upload_file_to_s3(file_path, bucket_name, aws_region)


