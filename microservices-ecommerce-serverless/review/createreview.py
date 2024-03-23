import json
import boto3
from botocore.exceptions import ClientError
import time
from datetime import datetime


dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reviews2')

def lambda_handler(event, context):
    print(event)
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)
    username = body['username']
    product_slug = body['product_slug'] 
    description = body['description']
    rating = body['rating']
    fullname = body['fullname']
    userphoto = body['userphoto']
    
    review_id=str(int(time.time()*1000))
    
    # Create review in DynamoDB
    item = {
           'product_slug': product_slug,
           'review_id': review_id,
           'username': username,
           'rating': rating, 
           'description': description,
           'fullname': fullname,
           'userphoto': userphoto,
           'date_added': datetime.now().isoformat()
       }

    table.put_item(
       Item=item
    )
    
    print(item)

    # Construct response
    response = {
        "statusCode": 200,
        "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
        "body": json.dumps({"message": "Review posted", "review": item})
    }

    return response