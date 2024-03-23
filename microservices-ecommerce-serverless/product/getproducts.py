import json
import boto3
from botocore.exceptions import ClientError
import base64
import time
import io
from datetime import datetime


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('products')
s3 = boto3.client('s3')
BUCKET_NAME='microservices-ecommerce-app'
CLOUDFRONT_URL = 'https://dn2aztcn1xe1u.cloudfront.net'

def lambda_handler(event, context):
    print(event)
    
    response = table.scan()
    items = response['Items']
    
    # Return response
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin" : "*",
            "Access-Control-Allow-Methods" : "*" 
        },
        "body": json.dumps({"results": items})
    }