import os
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import imghdr
import base64
import boto3

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") 
app.config['BUCKET_NAME'] = os.getenv("BUCKET_NAME") 
app.config['CLOUDFRONT_URL'] = os.getenv("CLOUDFRONT_URL")
app.config['STORAGE_PROVIDER']=os.getenv("STORAGE_PROVIDER")
app.config['AWS_ACCESS_KEY'] = os.getenv("AWS_ACCESS_KEY")
app.config['AWS_SECRET_KEY'] = os.getenv("AWS_SECRET_KEY")
app.config['STORAGE_HOST'] = os.getenv("STORAGE_HOST")
app.config['STORAGE_PORT'] = os.getenv("STORAGE_PORT")
app.config['STORAGE_HOST'] = os.getenv("STORAGE_HOST")
app.config['STORAGE_PORT'] = os.getenv("STORAGE_PORT")
app.config['STORAGE_HOST_EXT'] = os.getenv("STORAGE_HOST_EXT")
app.config['STORAGE_PORT_EXT'] = os.getenv("STORAGE_PORT_EXT")
app.config['SQLALCHEMY_DATABASE_URI']  = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
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

def s3uploading(filename):
    if app.config['STORAGE_PROVIDER']=='minio':
        storage_endpoint='http://'+app.config['STORAGE_HOST']+':'+app.config['STORAGE_PORT']
        s3 = boto3.client('s3', endpoint_url=storage_endpoint, aws_access_key_id=app.config['AWS_ACCESS_KEY'],
                                aws_secret_access_key=app.config['AWS_SECRET_KEY'])
    else:
        s3 = boto3.client('s3', aws_access_key_id=app.config['AWS_ACCESS_KEY'],
                            aws_secret_access_key=app.config['AWS_SECRET_KEY'])
                       
    bucket = app.config['BUCKET_NAME']
    path_filename_disk = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    path_filename_s3 = "photos/" + filename
    print(path_filename_s3)
    s3.upload_file(path_filename_disk, bucket, path_filename_s3)  
    if app.config['STORAGE_PROVIDER']=='minio':
        url= 'http://'+app.config['STORAGE_HOST_EXT']+':'+app.config['STORAGE_PORT_EXT']+"/"+app.config['BUCKET_NAME']+"/"+path_filename_s3
    else:
        url = app.config['CLOUDFRONT_URL']+'/'+path_filename_s3
    return url

@app.route('/api/products', methods=['GET'])
def products():
    items = []
    for row in Product.query.all():
        items.append(row.to_json())

    response = jsonify({'results': items})
    return response

#curl -X POST -F "name=Product 1" -F "slug=product-1" -F "description=This is product 1" -F "price=49.99" -F "image=@product1.jpg" http://localhost:5002/api/product/create
@app.route('/api/product/create', methods=['POST'])
def post_create():
    name = request.form.get('name') 
    slug = request.form.get('slug')
    description = request.form.get('description')
    price = request.form.get('price')
    image = request.files.get('image')

    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    uploadedFileURL = s3uploading(filename)

    item = Product()
    item.name = name
    item.slug = slug
    item.image = uploadedFileURL
    item.price = price
    item.description=description

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Product added', 'product': item.to_json()})
    return response


@app.route('/api/product/<slug>', methods=['GET'])
def product(slug):
    item = Product.query.filter_by(slug=slug).first()
    if item is not None:
        response = jsonify({'result': item.to_json()})
    else:
        response = jsonify({'message': 'Cannot find product'}), 404
    return response

@app.route('/api/productid/<id>', methods=['GET'])
def productid(id):
    item = Product.query.filter_by(id=id).first()
    if item is not None:
        response = jsonify({'result': item.to_json()})
    else:
        response = jsonify({'message': 'Cannot find product'}), 404
    return response


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/healthcheck', methods=['GET'])
def health_check():
    return make_response(jsonify({'message': 'Healthy'}), 200)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
