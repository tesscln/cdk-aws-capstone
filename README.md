# CDK stack for data ingestion pipeline matching IoT sensors data to a 3D CAD asset. 

## Introduction

## How to run the cdk

First of all, log into the terminal using your credential keys.

Clone the repo locally.


To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

## Deploying the stack

You can run '''python deploy.py'''.

1. Enter your AWS-REGION and AWS ACCOUNT_ID.

2. Enter a number of properties. This number should correspond to the number of data streams you would like to match to your 3D object. You can specify the properties data types and unit.

3. Enter the number of assets you would like to create. You then can enter the asset names and link them to the properties you want. 

4. Enter the number of MQTT topics you would like to subscribe to. Then, enter their names.

5. Enter the number of IoT Core rules you want to create. Typically, you should create one rule per asset, to send the data streams from a specific MQTT topic to one asset in IoT SiteWise. Link the right MQTT topic to each asset and specify the according sensor data name (schema below). 

A MQTT topic is a json file similar to this: 

{
  "sensorname": datavalue,
  "timeInSeconds": "timevalue",
  "_id_": "id"
}

The CDK will now deploy and created all the above.


## Uploading a 3D asset

You can run '''python upload_object.py'''.

It will ask you to enter the file path to your .usd file. It will then ask you for the bucket name to which you upload the file. This bucket is created previously with the cdk and should have the name 'assetmodel-usdfilebucket'. You should find it in the outputs of the cdk as well, either on your terminal or in CloudFormation directly. 


## Deleting the stack

If you want to delete the stack, you can do so in the CloudFormation console. However, you have to ensure before that the S3 bucket called 'asset-model-usdfilebucket' is emptied. 