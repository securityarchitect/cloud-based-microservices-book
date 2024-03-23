import json
import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
#import jwt

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ordersn')
#JWT_SECRET = 'mysecretkey'

# def validate_token(token):
#     validate_token = lambda token: jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
#     try:
#         payload = validate_token(token)
#         print('Token valid') 
#         return True
#     except jwt.ExpiredSignatureError:
#         print('Token expired') 
#         return False
#     except jwt.InvalidTokenError:
#         print('Invalid token')
#         return False
    
def lambda_handler(event, context):
    print(event)
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)
    username = body['username']
    #token = body['token']
    #is_valid = validate_token(token)

    response = table.query(KeyConditionExpression=Key('username').eq(username))
    orders = response['Items']
    print(orders)

    orderslist=[]
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
        for order in orders:
            if order['is_open']==False:
                orderslist.append(order)
    
    # Construct response
    response = {
            "statusCode": 200,
            "headers": {
                    "Access-Control-Allow-Origin" : "*",
                    "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "Order found", "result": orderslist})
        }

    return response