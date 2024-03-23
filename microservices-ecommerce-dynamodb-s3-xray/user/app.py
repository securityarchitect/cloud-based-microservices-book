import os
from flask import Flask, send_from_directory, send_file
from flask_login import LoginManager
from datetime import datetime
from flask_login import UserMixin
from passlib.hash import sha256_crypt
from flask import make_response, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from passlib.hash import sha256_crypt
from flask import g
from flask.sessions import SecureCookieSessionInterface
from flask_login import user_loaded_from_header
import time, random
import avinit
import base64
import boto3
from boto3.session import Session
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, UTCDateTimeAttribute
from pynamodb.connection import Connection
import uuid
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'
app.config['REGION'] = 'us-west-2'
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['BUCKET_NAME'] = 'microservices-ecommerce-app'
app.config['CLOUDFRONT_URL'] = 'https://dn2aztcn1xe1u.cloudfront.net'
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

plugins = ('EC2Plugin',)
xray_recorder.configure(service='User Service', plugins=plugins, sampling=False)
XRayMiddleware(app, xray_recorder)
patch_all()


login_manager.init_app(app)

class User(Model):    
    class Meta:
        table_name = "users1"
        region = "us-west-2"
        aws_access_key_id = app.config['AWS_ACCESS_KEY']
        aws_secret_access_key = app.config['AWS_SECRET_KEY']
    
    username = UnicodeAttribute(hash_key=True)  
    email = UnicodeAttribute()
    first_name = UnicodeAttribute()
    last_name = UnicodeAttribute()
    password = UnicodeAttribute() 
    photo = UnicodeAttribute()
    is_admin = BooleanAttribute()
    authenticated = BooleanAttribute()
    api_key = UnicodeAttribute()
    date_added = UTCDateTimeAttribute(default=datetime.utcnow)
    date_updated = UTCDateTimeAttribute()

    def encode_api_key(self):
        self.api_key = self.username+'@'+str(uuid.uuid4())

    def encode_password(self):
        self.password = sha256_crypt.hash(self.password)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False  

    def get_id(self):
        return str(self.username)

    def to_json(self):
        return {
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'email': self.email,
            'photo': self.photo,
            'api_key': self.api_key,
            'is_active': True,
            'is_admin': self.is_admin
        }

# Create the DynamoDB table if needed
if not User.exists():
    User.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return "Unauthorized", 401


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        splitkey = api_key.split('@')
        try:
            user = User.get(splitkey[0])
            if user.api_key==api_key:
                return user
        except:
            return None        
    return None

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

@app.route('/api/user/create', methods=['POST'])
def post_register():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    username = request.form['username']

    password = sha256_crypt.hash((str(request.form['password'])))

    name=first_name+' '+ last_name
    filename = "user"+str(int(time.time()*1000))+".png"
    imgpath=os.path.join(app.config['UPLOAD_FOLDER'], filename)
    r = lambda: random.randint(0,255)
    colors=[]
    colors.append('#%02X%02X%02X' % (r(),r(),r()))
    avinit.get_png_avatar(name, output_file=imgpath, colors=colors)

    uploadedFileURL = s3uploading(filename)

    # Create new user
    user = User(
        username = username,
        email = email,
        first_name = first_name,
        last_name = last_name,
        password = password,
        photo = uploadedFileURL,
        is_admin = False,
        authenticated = True,
        api_key = '',
        date_added = datetime.utcnow(),
        date_updated = datetime.utcnow()
    )
    
    # Save to DynamoDB
    user.save() 

    response = jsonify({'message': 'User added', 'result': user.to_json()})

    return response


@app.route('/api/user/login', methods=['POST'])
def post_login():
    username = request.form['username']
    try:
        user = User.get(username)
    except:  
        return make_response(jsonify({'message': 'User not found'}), 401)

    if user:
        if sha256_crypt.verify(str(request.form['password']), user.password):
            user.encode_api_key()
            user.save()
            login_user(user)

            return make_response(jsonify({'message': 'Logged in', 'user': user.to_json()}))

    return make_response(jsonify({'message': 'Not logged in'}), 401)


@app.route('/api/user/logout', methods=['POST'])
def post_logout():
    if current_user.is_authenticated:
        logout_user()
        return make_response(jsonify({'message': 'You are logged out'}))
    return make_response(jsonify({'message': 'You are not logged in'}))


@app.route('/api/user/<username>/exists', methods=['GET'])
def get_username(username):
    try:
        item = User.get(username)
    except:  
        return make_response(jsonify({'message': 'User not found'}), 401)

    if item is not None:
        response = jsonify({'result': True})
    else:
        response = jsonify({'message': 'Cannot find username'}), 404
    return response

@login_required
@app.route('/api/user', methods=['GET'])
def get_user():
    if current_user.is_authenticated:
        return make_response(jsonify({'result': current_user.to_json()}))

    return make_response(jsonify({'message': 'Not logged in'})), 401   

@app.route('/api/user/<username>', methods=['GET'])
def userid(username):
    try:
        item = User.get(username)
    except DoesNotExist:  
        return make_response(jsonify({'message': 'User not found'}), 401)

    if item is not None:
        response = jsonify({'result': item.to_json()})
    else:
        response = jsonify({'message': 'Cannot find user'}), 404
    return response


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
    g.login_via_header = True


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)