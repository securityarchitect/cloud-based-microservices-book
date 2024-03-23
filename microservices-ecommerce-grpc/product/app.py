import os
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
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
app.config['SQLALCHEMY_DATABASE_URI']  = 'mysql+pymysql://'+app.config['MYSQL_RDS_USER']+':'+app.config['MYSQL_RDS_PASSWORD']+'@'+app.config['MYSQL_RDS_ENDPOINT']+':3306/product'
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'
db.init_app(app)
migrate = Migrate(app, db)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    price = db.Column(db.Float, default=0)
    image = db.Column(db.String(255), unique=False, nullable=True)
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'slug': self.slug,
            'price': self.price,
            'image': self.image
        }

