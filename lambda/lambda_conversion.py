import os
import boto3 # type: ignore
import tempfile
import subprocess
import logging
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        region = os.environ['AWS_REGION']

        instance_id = os.environ['INSTANCE_ID']
    
        logger.info(f"Running in AWS Region: {region}")
        logger.info(f"Starting EC2 instance: {instance_id}")

        print(f"Running in AWS Region: {region}")
        print(f"Starting EC2 Instance: {instance_id}")

        ec2 = boto3.client('ec2', region_name=region)

        response = ec2.start_instances(
          InstanceIds=[instance_id]
     )
    
        logger.info(f"EC2 instance {instance_id} started successfully. Response: {response}")

        return response

    except NoCredentialsError:
        logger.error("No AWS credentials were found.")
        
    except ClientError as e:
        logger.error(f"A client error occurred: {e}")
    
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
