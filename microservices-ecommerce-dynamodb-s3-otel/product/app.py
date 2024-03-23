import os
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import jsonify, request
from datetime import datetime
from werkzeug.utils import secure_filename
import base64
import boto3
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.connection import Connection
import uuid
from opentelemetry import trace, baggage
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.context import attach, detach
from opentelemetry.context.context import Context
from opentelemetry.propagate import extract
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.trace import SpanKind, TraceFlags
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    BatchSpanProcessor,
)
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

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

service_name = 'ecommerce-product'
agent_host = os.environ.get('AGENT_HOST', 'localhost')
agent_port = os.environ.get('AGENT_PORT', '6831')

trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: service_name})
    )
)

jaeger_exporter = JaegerExporter(
    agent_host_name = agent_host,
    agent_port = int(agent_port),
)

trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
tracer = trace.get_tracer('ecommerce-product')

class Product(Model):    
    class Meta:
        table_name = "products"
        region = "us-west-2"
        aws_access_key_id = app.config['AWS_ACCESS_KEY']
        aws_secret_access_key = app.config['AWS_SECRET_KEY']
    
    slug = UnicodeAttribute(hash_key=True)  
    name = UnicodeAttribute()
    description = UnicodeAttribute()
    image = UnicodeAttribute()
    price = UnicodeAttribute()
    date_added = UTCDateTimeAttribute(default=datetime.utcnow)
    date_updated = UTCDateTimeAttribute()

    def to_json(self):
        return {
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image': self.image
        }

# Create the DynamoDB table if needed
if not Product.exists():
    Product.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

def s3uploading(filename):
    s3 = boto3.client('s3', aws_access_key_id=app.config['AWS_ACCESS_KEY'],
                            aws_secret_access_key=app.config['AWS_SECRET_KEY'])
                       
    bucket = app.config['BUCKET_NAME']
    path_filename_disk = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    path_filename_s3 = "photos/" + filename
    print(path_filename_s3)
    s3.upload_file(path_filename_disk, bucket, path_filename_s3)  
    url = app.config['CLOUDFRONT_URL']+'/'+path_filename_s3
    return url

@app.route('/api/products', methods=['GET'])
def products():
    # Scan with limit of max 50 items 
    products = Product.scan()
    print(products)
    items = []
    for item in products:
        print(item.to_json())
        items.append(item.to_json())
    return jsonify({
        "results": items
    })

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


    # Create new user
    item = Product(
        slug = slug,
        name = name,
        image = uploadedFileURL,
        price = price,
        description = description,
        date_added = datetime.utcnow(),
        date_updated = datetime.utcnow()
    )
    
    # Save to DynamoDB
    item.save() 

    response = jsonify({'message': 'Product added', 'product': item.to_json()})
    return response


@app.route('/api/product/<slug>', methods=['GET'])
def product(slug):
    try:
        item = Product.get(slug)
    except:
        response = jsonify({'message': 'Cannot find product'}), 404
    if item is not None:
        response = jsonify({'result': item.to_json()})
    else:
        response = jsonify({'message': 'Cannot find product'}), 404
    return response


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
