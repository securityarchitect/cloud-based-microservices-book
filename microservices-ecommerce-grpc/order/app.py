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
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['BUCKET_NAME'] = 'microservices-ecommerce-app'
app.config['CLOUDFRONT_URL'] = 'https://dn2aztcn1xe1u.cloudfront.net'
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'
app.config['MYSQL_RDS_ENDPOINT'] = 'database-1.czqnyxmkvtxg.us-west-2.rds.amazonaws.com'
app.config['MYSQL_RDS_USER'] = 'admin' 
app.config['MYSQL_RDS_PASSWORD'] = 'S9c1Zl6tC93AuTfKCLLV'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://'+app.config['MYSQL_RDS_USER']+':'+app.config['MYSQL_RDS_PASSWORD']+'@'+app.config['MYSQL_RDS_ENDPOINT']+':3306/orderdb'
app.config['SQLALCHEMY_ECHO'] = True

USER_SERVICE_URL='http://127.0.0.1:5001'

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

