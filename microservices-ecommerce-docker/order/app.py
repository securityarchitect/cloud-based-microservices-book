import os
from flask import Flask
from flask_migrate import Migrate
from flask import jsonify, request, make_response
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import boto3

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") 
app.config['SQLALCHEMY_DATABASE_URI']  = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

USER_SERVICE_URL=os.getenv("USER_SERVICE_URL") #'http://user-service:5000'

db.init_app(app)
migrate = Migrate(app, db)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    items = db.relationship('OrderItem', backref='orderItem')
    is_open = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def create(self, user_id):
        self.user_id = user_id
        self.is_open = True
        return self

    def to_json(self):
        items = []
        amount=0
        for i in self.items:
            items.append(i.to_json())
            amount=amount+i.price*i.quantity
            amount=round(amount,2)

        return {
            'id': self.id,
            'items': items,
            'is_open': self.is_open,
            'user_id': self.user_id,
            'date_added': self.date_added.strftime("%b %d, %Y"),
            'amount': amount
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer)
    price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

    def to_json(self):
        return {
            'price': self.price,
            'product': self.product_id,
            'quantity': self.quantity
        }


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
    p_id = int(request.form['product_id'])
    qty = int(request.form['qty'])
    price = float(request.form['price'])
    u_id = int(user['id'])

    known_order = Order.query.filter_by(user_id=u_id, is_open=1).first()

    if known_order is None:
        known_order = Order()
        known_order.is_open = True
        known_order.user_id = u_id

        order_item = OrderItem(p_id, qty, price)
        known_order.items.append(order_item)
    else:
        found = False

        for item in known_order.items:
            if item.product_id == p_id:
                found = True
                item.quantity += qty

        if found is False:
            order_item = OrderItem(p_id, qty, price)
            known_order.items.append(order_item)

    db.session.add(known_order)
    db.session.commit()
    response = jsonify({'result': known_order.to_json()})
    return response


@app.route('/api/order', methods=['GET'])
def order():
    api_key = request.headers.get('Authorization')

    response = UserClient.get_user(api_key)

    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

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

    order_model = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    order_model.is_open = 0

    db.session.add(order_model)
    db.session.commit()

    response = jsonify({'result': order_model.to_json()})
    return response

@app.route('/api/cart', methods=['GET'])
def cart():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

    if open_order is None:
        response = jsonify({'message': 'No order found', 'result': []})
    else:
        items=[]
        for item in open_order.items:
            items.append(item.to_json())

        response = jsonify({'result': items})
    return response

@app.route('/api/orders', methods=['GET'])
def orders():
    api_key = request.headers.get('Authorization')
    response = UserClient.get_user(api_key)
    if not response:
        return make_response(jsonify({'message': 'Not logged in'}), 401)

    user = response['result']
    orders = Order.query.filter_by(user_id=user['id'], is_open=0)

    if orders is None:
        response = jsonify({'message': 'No order found', 'result': []})
    else:
        items=[]
        for item in orders:
            items.append(item.to_json())

        response = jsonify({'result': items})
    return response

@app.route('/healthcheck', methods=['GET'])
def health_check():
    return make_response(jsonify({'message': 'Healthy'}), 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
