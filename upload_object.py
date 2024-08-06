import os
import boto3 # type: ignore
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

def create_s3_bucket(bucket_name, region):
    try:
        s3_client = boto3.client('s3', region_name=region)
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print(f"Bucket '{bucket_name}' created successfully in region '{region}'.")
    except ClientError as e:
        print(f"Failed to create bucket '{bucket_name}'. Error: {e}")
        return False
    return True


def upload_file_to_s3(file_path, bucket_name, region):
    s3_client = boto3.client('s3', region_name=region)
    try:
        s3_client.upload_file(file_path, bucket_name, os.path.basename(file_path))
        print(f"File {file_path} uploaded successfully to bucket '{bucket_name}'.")
    except Exception as e:
        print(f"Failed to upload file: {str(e)}")


def main():
    # Ask user for the file path
    file_path = input("Enter the file path to upload the 3D object (it needs to be in .usd format): ")

    # Ask user for the bucket name
    bucket_name = os.environ.get('BUCKET_NAME')

    # Ask user for the AWS region
    aws_region = os.environ.get('AWS_REGION')

    # Create the S3 bucket
    if create_s3_bucket(bucket_name, aws_region):
        # Upload the file
        upload_file_to_s3(file_path, bucket_name)


if __name__ == "__main__":
    main()
