import json
import boto3
from botocore.exceptions import ClientError
import base64
import time
import io
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reviews2')

def lambda_handler(event, context):
    print(event)
    
    slug = event['pathParameters']['slug']

    # Get product from DynamoDB    
    response = table.query(KeyConditionExpression=Key('product_slug').eq(slug))
    #response = table.scan(
    #    FilterExpression=Attr('product_slug').eq(slug)
    #)

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