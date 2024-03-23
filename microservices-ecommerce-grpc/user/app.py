import os
from flask import Flask, send_from_directory, send_file
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from passlib.hash import sha256_crypt
from flask import make_response, request, jsonify
import time, random

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
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://'+app.config['MYSQL_RDS_USER']+':'+app.config['MYSQL_RDS_PASSWORD']+'@'+app.config['MYSQL_RDS_ENDPOINT']+':3306/user'
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'


db.init_app(app)
migrate = Migrate(app, db)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(255), unique=False, nullable=True)
    last_name = db.Column(db.String(255), unique=False, nullable=True)
    password = db.Column(db.String(255), unique=False, nullable=False)
    photo = db.Column(db.String(255), unique=False, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    authenticated = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(255), unique=True, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def encode_api_key(self):
        self.api_key = sha256_crypt.hash(self.username + str(datetime.utcnow))

    def encode_password(self):
        self.password = sha256_crypt.hash(self.password)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def to_json(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'email': self.email,
            'photo': self.photo,
            'id': self.id,
            'api_key': self.api_key,
            'is_active': True,
            'is_admin': self.is_admin
        }


