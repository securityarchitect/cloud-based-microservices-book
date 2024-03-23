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
    product_slug = body['product_slug'] 
    qty = int(body['qty'])
    price = float(body['price'])
    image = body['image'] 
    name = body['name'] 
    
    response = table.query(KeyConditionExpression=Key('username').eq(username))
    orders = response['Items']
    print(orders)

    known_order=None
    if orders is None:
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "No order found", "result": []})
        }
        return response
    else:
        items=[]
        for order in orders:
            if order['is_open']==True:
                known_order=order

    if known_order is None:
        itemslist=[]
        itemslist.append({'product_slug': product_slug, 'quantity': qty, 'price': price, 'image': image, 'name': name})
        order_id=str(int(time.time()*1000))

        known_order = {
           'username': username,
           'order_id': order_id, 
           'is_open': True,
           'items': json.dumps(itemslist),
           'date_added': datetime.now().isoformat()
        }

        table.put_item(
            Item=known_order
        )
    else:
        found = False
        itemslist=json.loads(known_order['items'])
        print("Items in existing order: ", itemslist)
        newitemslist=[]
        for item in itemslist:
            if item['product_slug'] == product_slug:
                found = True
                item['quantity'] = int(item['quantity'])+qty
                print("Known order exists and item found")
            newitemslist.append(item)
        
        if found is False:
            print("Known order exists but item not found")
            newitemslist.append({'product_slug': product_slug, 'quantity': qty, 'price': price, 'image': image, 'name': name})
        
        print("New items list", newitemslist)
        known_order['items']=json.dumps(newitemslist)
        table.put_item(
            Item=known_order
        )

    # Construct response
    response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Methods" : "*" 
            },
            "body": json.dumps({"message": "Order found", "result": known_order})
        }

    return response