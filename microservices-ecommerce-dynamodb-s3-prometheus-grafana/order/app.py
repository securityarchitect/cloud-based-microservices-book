import os
from flask import Flask
from flask_migrate import Migrate
from flask import jsonify, request, make_response
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.connection import Connection
import uuid
import json
import time 


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['BUCKET_NAME'] = 'microservices-ecommerce-app'
app.config['CLOUDFRONT_URL'] = 'https://dn2aztcn1xe1u.cloudfront.net'
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'
app.config['ENV'] = "development"
app.config['DEBUG'] = True

USER_SERVICE_URL='http://localhost:5001'



class Order(Model):    
    class Meta:
        table_name = "ordersn"
        region = "us-west-2"
        aws_access_key_id = app.config['AWS_ACCESS_KEY']
        aws_secret_access_key = app.config['AWS_SECRET_KEY']
    
    username = UnicodeAttribute(hash_key=True)
    order_id = UnicodeAttribute(range_key=True)
    is_open = BooleanAttribute()
    items = UnicodeAttribute()
    date_added = UTCDateTimeAttribute(default=datetime.utcnow)

    def to_json(self):
        items = []
        amount=0
        for i in json.loads(self.items):
            items.append(i)
            amount=amount+float(i['price'])*float(i['quantity'])
            amount=round(amount,2)

        return {
            'items': items,
            'order_id': self.order_id,
            'is_open': self.is_open,
            'username': self.username,
            'date_added': self.date_added.strftime("%b %d, %Y"),
            'amount': amount
        }

# Create the DynamoDB table if needed
if not Order.exists():
    Order.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)


class UserClient:
    @staticmethod
    def get_user(api_key):
        headers = {
            'Authorization': api_key
        }
        response = requests.request(method="GET", url=USER_SERVICE_URL+'/api/user', headers=headers)
        if response.status_code == 401:
            return False
        user = response.json()
        return user


@app.route('/api/order/add-item', methods=['POST'])
def order_add_item():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    product_slug = request.form['product_slug']
    qty = int(request.form['qty'])
    price = float(request.form['price'])
    username = user['username']

    orders = Order.scan(Order.username.startswith(username))
    print(orders)

    known_order=None
    if orders is None:
        response = jsonify({'message': 'No order found', 'result': []})
    else:
        items=[]
        for order in orders:
            if order.is_open==True:
                known_order=order

    if known_order is None:
        itemslist=[]
        order_id=str(int(time.time()*1000))
        known_order = Order(
            username = username,
            order_id=order_id,
            is_open = True,
            date_added = datetime.utcnow()
        )
    
        itemslist.append({'product_slug': product_slug, 'quantity': qty, 'price': price})
        known_order.items=json.dumps(itemslist)
    else:
        found = False
        itemslist=json.loads(known_order.items)
        print("Items in existing order: ", itemslist)
        newitemslist=[]
        for item in itemslist:
            if item['product_slug'] == product_slug:
                found = True
                item['quantity'] = int(item['quantity'])+qty
            newitemslist.append(item)
        
        if found is False:
            newitemslist.append({'product_slug': product_slug, 'quantity': qty, 'price': price})
        
        known_order.items=json.dumps(newitemslist)

    known_order.save()
    response = jsonify({'result': known_order.to_json()})
    return response


@app.route('/api/order', methods=['GET'])
def order():
    api_key = request.headers.get('Authorization')

    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    print("Getting open order for user:", user['username'])
    orders = Order.scan(Order.username.startswith(user['username']))
    print(orders)
    open_order=None
    for order in orders:
        print(order.to_json())
        if order.is_open==True:
            open_order=order

    if open_order is None:
        response = jsonify({'message': 'No order found'})
    else:
        response = jsonify({'result': open_order.to_json()})
    return response


@app.route('/api/order/checkout', methods=['POST'])
def checkout():
    api_key = request.headers.get('Authorization')

    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']

    orders = Order.scan(Order.username.startswith(user['username']))
    print(orders)
    open_order=None
    for order in orders:
        if order.is_open==True:
            open_order=order
            open_order.is_open=False
            open_order.save()
    
    response = jsonify({'result': open_order.to_json()})
    return response

@app.route('/api/cart', methods=['GET'])
def cart():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    print("Getting cart for user:", user['username'])
    orders = Order.scan(Order.username.startswith(user['username']))
    print(orders)

    if orders is None:
        response = jsonify({'message': 'No order found', 'result': []})
    else:
        items=[]
        orderitems=[]
        for order in orders:
            print(order.to_json())
            if order.is_open==True:
                orderitems=order.to_json()['items']
                #items.append()

        response = jsonify({'result': orderitems})
        print(response)
    return response

@app.route('/api/orders', methods=['GET'])
def orders():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    print("Getting all orders for user:", user['username'])
    orders = Order.scan(Order.username.startswith(user['username']))
    print(orders)

    if orders is None:
        response = jsonify({'message': 'No order found', 'result': []})
    else:
        items=[]
        for order in orders:
            if order.is_open==False:
                items.append(order.to_json())

        response = jsonify({'result': items})
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
