import json
import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ordersn')

def lambda_handler(event, context):
    print(event)
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)
    username = body['username']
    
    response = table.query(KeyConditionExpression=Key('username').eq(username))
    orders = response['Items']
    print(orders)

    open_order=None
    if orders is None:
        response = {
            "statusCode": 200,
            "body": json.dumps({"message": "No order found", "result": []})
        }
        return response
    else:
        for order in orders:
            if order['is_open']==True:
                open_order=order
    
    if open_order is None:
        response = {
            "statusCode": 200,
            "body": json.dumps({"message": "No order found", "result": []})
        }
        return response
    else:
        response = {
                "statusCode": 200,
                "body": json.dumps({"message": "Open order found", "result": open_order})
            }
    
        return response