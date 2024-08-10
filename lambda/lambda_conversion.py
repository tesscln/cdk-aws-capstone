import os
import boto3 # type: ignore
import tempfile
import subprocess
from botocore.exceptions import NoCredentialsError, ClientError # type: ignore

ec2 = boto3.client('ec2')

def lambda_handler(event, context):

    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Purpose',
                'Values': ['USDToGLTFConversion']
            }
        ]
    )

    # Extract the instance ID
    instance_ids = [instance['InstanceId']
                    for reservation in response['Reservations']
                    for instance in reservation['Instances']]

    # Check if there is at least one instance found
    if not instance_ids:
        return {
            'statusCode': 404,
            'body': 'No instance found with the specified tag.'
        }

    # Start the instance
    ec2.start_instances(InstanceIds=instance_ids)

    return {
        'statusCode': 200,
        'body': f'Started instance(s): {instance_ids}'
    }