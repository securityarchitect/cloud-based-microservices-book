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
            "headers": {
                    "Access-Control-Allow-Origin" : "*",
                    "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "No order found", "result": []})
        }
        return response
    else:
        orderitems=[]
        for order in orders:
            if order['is_open']==True:
                open_order=order
                open_order['is_open']=False
                table.put_item(
                    Item=open_order
                )
                
    
    # Construct response
    response = {
            "statusCode": 200,
            "headers": {
                    "Access-Control-Allow-Origin" : "*",
                    "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "Order found", "result": open_order})
        }

    return response