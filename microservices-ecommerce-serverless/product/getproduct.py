import json
import boto3
from botocore.exceptions import ClientError
import base64
import time
import io
from datetime import datetime
from boto3.dynamodb.conditions import Key


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('products')
s3 = boto3.client('s3')
BUCKET_NAME='microservices-ecommerce-app'
CLOUDFRONT_URL = 'https://dn2aztcn1xe1u.cloudfront.net'

def lambda_handler(event, context):
    print(event)
    
    slug = event['pathParameters']['slug']

    # Get product from DynamoDB    
    response = table.query(KeyConditionExpression=Key('slug').eq(slug))
    item = response['Items'][0] if response['Items'] else None

    # Return response
    if item:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"result": item})
        }
    else:
        return {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "Product not found"})  
        }