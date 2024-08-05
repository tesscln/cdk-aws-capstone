import boto3 # type: ignore
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError # type: ignore

def upload_file_to_s3(file_path, bucket_name):
    s3 = boto3.client('s3')
    try:
        file_name = os.path.basename(file_path)
        s3.upload_file(file_path, bucket_name, file_name)
        print(f"File {file_name} uploaded successfully to bucket {bucket_name}.")
    except FileNotFoundError:
        print("The file was not found.")
    except NoCredentialsError:
        print("Credentials not available.")
    except PartialCredentialsError:
        print("Incomplete credentials.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    file_path = input("Enter the file path to upload: ")
    bucket_name = input("Enter the S3 bucket name: ")
    if os.path.isfile(file_path):
        upload_file_to_s3(file_path, bucket_name)
    else:
        print("Invalid file path provided.")

if __name__ == "__main__":
    main()