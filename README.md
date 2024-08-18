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

Now, you can run '''python deploy.py'''
It will ask you to enter your AWS-REGION and AWS ACCOUNT_ID.
Then, it will ask you for a number of properties. This number should correspond to the number of data streams you would like to match to your 3D object. 

If you want to delete the stack, you can do so in the CloudFormation console. However, you have to ensure before that the S3 bucket called 'asset-model-usdfilebucket' is emptied. 