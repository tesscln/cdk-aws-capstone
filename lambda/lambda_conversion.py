import os
import boto3 # type: ignore
import tempfile
import subprocess
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore


def lambda_handler(event, context):

    region = os.environ['AWS_REGION']

    instance_id = os.environ['INSTANCE_ID']

    print(f"Running in AWS Region: {region}")
    print(f"Starting EC2 Instance: {instance_id}")

    ec2 = boto3.client('ec2', region_name=region)

    response = ec2.start_instances(
        InstanceIds=[instance_id]
    )

    return response