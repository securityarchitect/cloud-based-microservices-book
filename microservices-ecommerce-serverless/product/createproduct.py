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
    
    # Get product details from request
    body = event['body'].strip()
    body=body.replace('\n','')
    body=json.loads(body)
    name = body['name']
    slug = body['slug'] 
    description = body['description']
    price = body['price']
    image = body['image']
    filename=body['filename']
    image_data = base64.b64decode(image) 
    image_object = io.BytesIO(image_data)
    
    # Upload image to S3    
    path_filename_s3 = "photos/" + filename
    s3.upload_fileobj(image_object, BUCKET_NAME, path_filename_s3)
    url = CLOUDFRONT_URL+'/'+path_filename_s3

    # Create product in DynamoDB
    item = {
           'slug': slug,
           'name': name,
           'description': description,
           'price': price,
           'image': url,
           'date_added': datetime.now().isoformat()
       }
       
    table.put_item(
       Item=item
    )
    
    print(item)

    # Construct response
    response = {
        "statusCode": 200,
        "body": json.dumps({"message": "Product created", "product": item})
    }

    return response