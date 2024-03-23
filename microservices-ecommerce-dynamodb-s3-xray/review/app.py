import os
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import jsonify, request
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.connection import Connection
import uuid
import time
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['BUCKET_NAME'] = 'microservices-ecommerce-app'
app.config['CLOUDFRONT_URL'] = 'https://dn2aztcn1xe1u.cloudfront.net'
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

plugins = ('EC2Plugin',)
xray_recorder.configure(service='Review Service', plugins=plugins, sampling=False)
XRayMiddleware(app, xray_recorder)
patch_all()

class Review(Model):    
    class Meta:
        table_name = "reviews"
        region = "us-west-2"
        aws_access_key_id = app.config['AWS_ACCESS_KEY']
        aws_secret_access_key = app.config['AWS_SECRET_KEY']
    
    product_slug = UnicodeAttribute(hash_key=True)  
    review_id = UnicodeAttribute(range_key=True)
    username = UnicodeAttribute()
    description = UnicodeAttribute()
    rating = UnicodeAttribute()
    date_added = UTCDateTimeAttribute(default=datetime.utcnow)
    date_updated = UTCDateTimeAttribute()

    def to_json(self):
        return {
            'username': self.username,
            'product_slug': self.product_slug,
            'review_id': self.review_id,
            'rating': self.rating,
            'description': self.description,
            'date_added': self.date_added.strftime("%b %d, %Y")
        }

# Create the DynamoDB table if needed
if not Review.exists():
    Review.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)
    

@app.route('/api/review/add', methods=['POST'])
def post_create():
    username = request.form.get('username') 
    product_slug = request.form.get('product_slug') 
    rating = request.form.get('rating')
    description = request.form.get('review')
    review_id=str(int(time.time()*1000))
    # Create new review
    item = Review(
        product_slug = product_slug,
        review_id = review_id,
        username = username,
        rating = rating,
        description = description,
        date_added = datetime.utcnow(),
        date_updated = datetime.utcnow()
    )
    item.save()

    response = jsonify({'message': 'Review added', 'review': item.to_json()})
    return response


@app.route('/api/reviews/<product_slug>', methods=['GET'])
def reviews(product_slug):
    #return {}, 500 # Inject fault: HTTP Internal Server Error
    reviews = Review.scan(Review.product_slug.startswith(product_slug))
    items = []
    for item in reviews:
        print(item.to_json())
        items.append(item.to_json())
    return jsonify({
        "results": items
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
