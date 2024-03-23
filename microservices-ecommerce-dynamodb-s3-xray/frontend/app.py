import os
import requests
from flask import Flask
from flask_migrate import Migrate
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask import session, request
import json, time
from datetime import datetime, timedelta
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
import logging
import boto3
from watchtower import CloudWatchLogHandler


login_manager = LoginManager()
bootstrap = Bootstrap()

app = Flask(__name__, static_folder='static') 
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['WTF_CSRF_SECRET_KEY'] = "sEWQkE9oYBiF5fVJnm278i7"
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'

plugins = ('EC2Plugin',)
xray_recorder.configure(service='Ecommerce Frontend', plugins=plugins, sampling=False)
XRayMiddleware(app, xray_recorder)
patch_all()


cloudwatch = boto3.client('cloudwatch', aws_access_key_id=app.config['AWS_ACCESS_KEY'],
                            aws_secret_access_key=app.config['AWS_SECRET_KEY'], region_name='us-west-2')


#logger = logging.getLogger()
#logger.setLevel(logging.INFO)
#logging.getLogger('aws_xray_sdk').setLevel(logging.INFO)

#USER_SERVICE_URL='http://localhost:5001'
#PRODUCT_SERVICE_URL='http://localhost:5002'
#ORDER_SERVICE_URL='http://localhost:5003'
#REVIEW_SERVICE_URL='http://localhost:5004'
USER_SERVICE_URL='http://172.31.22.221:5000'
PRODUCT_SERVICE_URL='http://172.31.23.59:5000'
ORDER_SERVICE_URL='http://172.31.24.13:5000'
REVIEW_SERVICE_URL='http://172.31.16.29:5000'

login_manager.init_app(app)
login_manager.login_message = "Please login"
login_manager.login_view = "login"



# Create CloudWatch Logs client
cw_logs_client = boto3.client('logs', aws_access_key_id=app.config['AWS_ACCESS_KEY'],
                            aws_secret_access_key=app.config['AWS_SECRET_KEY'], region_name='us-west-2')


# Log group and stream names
log_group_name = 'my-log-group'
log_stream_name = 'my-log-stream'

# Check if log group exists, if not then create it
log_groups = cw_logs_client.describe_log_groups()
log_group_exists = False
for group in log_groups['logGroups']:
    if group['logGroupName'] == log_group_name:
        log_group_exists = True
        break
if not log_group_exists: 
    cw_logs_client.create_log_group(logGroupName=log_group_name)

# Check if log stream exists, if not then create it  
log_streams = cw_logs_client.describe_log_streams(logGroupName=log_group_name)
log_stream_exists = False
for stream in log_streams['logStreams']:
    if stream['logStreamName'] == log_stream_name:
        log_stream_exists = True
        break
if not log_stream_exists:
    cw_logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name) 

# Create CloudWatch Logs handler
cw_handler = CloudWatchLogHandler(log_group=log_group_name, stream_name=log_stream_name, boto3_client=cw_logs_client)

# Configure logger and add handler 
logger = logging.getLogger()
logger.setLevel(logging.INFO)  
logger.addHandler(cw_handler)


class UserClient:
    @staticmethod
    def post_login(form):
        api_key = False
        payload = {
            'username': form.username.data,
            'password': form.password.data
        }
        url = USER_SERVICE_URL+'/api/user/login'
        response = requests.post( url=url, data=payload)
        if response:
           d = response.json()
           #print("This is response from user api: " + str(d))
           if d['user'] is not None:
               user = d['user']
        return user

    @staticmethod
    def get_user():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }

        url = USER_SERVICE_URL+'/api/user'
        response = requests.get(url=url, headers=headers)
        user = response.json()
        print(user)
        return user

    @staticmethod
    def get_user_with_username(username):
        response = requests.get(url=USER_SERVICE_URL+'/api/user/' + str(username))
        user = response.json()
        return user

    @staticmethod
    def post_user_create(form):
        user = False
        payload = {
            'email': form.email.data,
            'password': form.password.data,
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'username': form.username.data
        }
        url = USER_SERVICE_URL+'/api/user/create'
        response = requests.post(url=url, data=payload)
        if response:
            user = response.json()
        return user

    @staticmethod
    def does_exist(username):
        url = USER_SERVICE_URL+'/api/user/' + username + '/exists'
        response = requests.get(url=url)
        return response.status_code == 200


class ProductClient:
    @staticmethod
    def get_products():
        r = requests.get(PRODUCT_SERVICE_URL+'/api/products')
        products = r.json()
        return products

    @staticmethod
    def get_product(slug):
        response = requests.get(url=PRODUCT_SERVICE_URL+'/api/product/' + slug)
        product = response.json()
        return product

class OrderClient:
    @staticmethod
    def get_order():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = ORDER_SERVICE_URL+'/api/order'
        response = requests.get(url=url, headers=headers)
        order = response.json()
        return order

    @staticmethod
    def post_add_to_cart(username, product_slug, price, qty=1):
        payload = {
            'username': username,
            'product_slug': product_slug,
            'qty': qty,
            'price': price
        }
        url = ORDER_SERVICE_URL+'/api/order/add-item'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.post(url=url, data=payload, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def post_checkout():
        url = ORDER_SERVICE_URL+'/api/order/checkout'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.post(url=url, headers=headers)
        order = response.json()
        return order

    @staticmethod
    def get_order_from_session():
        default_order = {
            'items': {},
            'total': 0,
        }
        return session.get('order', default_order)
    
    @staticmethod
    def get_cart():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }

        r = requests.get(ORDER_SERVICE_URL+'/api/cart', headers=headers)
        products = r.json()
        return products

    @staticmethod
    def get_orders():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }

        r = requests.get(ORDER_SERVICE_URL+'/api/orders', headers=headers)
        orders = r.json()
        return orders


class ReviewClient:
    @staticmethod
    def post_review(username, product_slug, rating, review):
        payload = {
            'username': username,
            'product_slug': product_slug,
            'rating': rating,
            'review': review
        }
        url = REVIEW_SERVICE_URL+'/api/review/add'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }

        response = requests.post(url=url, data=payload, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def get_reviews(product_slug):
        try:
            headers = {
                'Authorization': 'Basic ' + session['user_api_key']
            }

            r = requests.get(REVIEW_SERVICE_URL+'/api/reviews/'+str(product_slug), headers=headers)
            reviews = r.json()
        except:
            reviews={}
            reviews['results']=[]
        return reviews

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    first_name = StringField('First name', validators=[DataRequired()])
    last_name = StringField('Last name', validators=[DataRequired()])
    email = StringField('Email address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class ItemForm(FlaskForm):
    product_id = HiddenField(validators=[DataRequired()])
    quantity = HiddenField(validators=[DataRequired()], default=1)


@login_manager.user_loader
def load_user(user_id):
    return None

def put_metric_data(namespace, metric_name, value, unit, dimensions):
    return cloudwatch.put_metric_data(
        Namespace=namespace,
        MetricData=[{
            'MetricName': metric_name,
            'Value': value, 
            'Unit': unit,
            'Dimensions': dimensions
            #'Timestamp': datetime.utcnow()
        }]
    )

def get_metric_data(namespace, metric_name, dimensions, metric_id):
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[{
            'Id': metric_id,
            'MetricStat': {
                'Metric': {
                    'Namespace': namespace, 
                    'MetricName': metric_name,
                    'Dimensions': dimensions  
                },
                'Period': 43200, 
                'Stat': 'Maximum' 
            }
        }],
        StartTime=datetime.utcnow() - timedelta(hours=12), 
        EndTime=datetime.utcnow()
    )
    print(namespace, metric_name, dimensions, metric_id)
    print(response)
    try:
        current_value = response['MetricDataResults'][0]['Values'][0]
    except:
        current_value=0
    return current_value

def get_user_name_photo():
    try:
        response = UserClient.get_user()
        user = response['result']
        user_name = user['first_name']+" "+user['last_name']
        user_photo = user['photo']
    except:
        user_name=''
        user_photo=''
        
    return user_name, user_photo

@app.route('/', methods=['GET'])
def home():
    #subsegment = xray_recorder.begin_subsegment('annotations')
    logger.info('Handling home page')
    if current_user.is_authenticated:
        session['order'] = OrderClient.get_order_from_session()
    
    try:
        products = ProductClient.get_products()
    except:
        products = {
            'results': []
        }

    document = xray_recorder.current_segment()
    if 'user' in session:
        document.put_annotation('user', session['user'])
        document.put_metadata('page', 'home page')
        document.put_metadata('user', session['user'])

    user_name, user_photo = get_user_name_photo()
    #xray_recorder.end_subsegment()
    return render_template('home.html', products=products, user_name = user_name, 
        user_photo=user_photo)

@app.route('/register', methods=['GET', 'POST'])
@xray_recorder.capture('register')
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data

            # Search for existing user
            user = UserClient.does_exist(username)
            if user:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create new user
                user = UserClient.post_user_create(form)
                if user:
                    flash('Thanks for registering, please login', 'success')
                    return redirect(url_for('login'))

        else:
            flash('Errors found', 'error')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@xray_recorder.capture('login')
def login():
    logger.info('Handling login')
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == "POST":
        #segment = xray_recorder.begin_segment('login_user')
        #segment.put_metadata('user', payload, 'user')
        #segment.put_annotation('username', form.username.data)
        if form.validate_on_submit():
            user = UserClient.post_login(form)
            print(user)
            if user:
                session['user_api_key'] = user['api_key']
                session['user'] = user

                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']

                flash('Welcome back, ' + user['first_name'], 'success')
                return redirect(url_for('home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
        #xray_recorder.end_segment()
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/product/<slug>', methods=['GET', 'POST'])
@xray_recorder.capture('productpage')
def product(slug):
    response = ProductClient.get_product(slug)
    item = response['result']
    form = ItemForm(product_id=item['slug'])

    reviewslist=[]

    print("Getting reviews for ", item['slug'])
    try:
        reviews=ReviewClient.get_reviews(item['slug'])
        for review in reviews['results']:
            reviewdict={}
            reviewdict['rating']=review['rating']
            reviewdict['description']=review['description']
            reviewdict['date_added']=review['date_added']
            reviewer=UserClient.get_user_with_username(review['username'])
            reviewdict['photo']=reviewer['result']['photo']
            reviewdict['user_name']=reviewer['result']['first_name']+' '+reviewer['result']['last_name']
            reviewslist.append(reviewdict)
    except:
        pass

    if request.method == "POST":
        start_time = time.time()
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('login'))
        order = OrderClient.post_add_to_cart(username=session['user']['username'], product_slug=item['slug'], price=item['price'], qty=1)
        session['order'] = order['result']
        dimensions = [{'Name': 'product_slug', 'Value': item['slug']}]
        metric_id = 'productAddToCart'+item['slug']
        metric_id = metric_id.replace('-', '')
        #current_value = get_metric_data('Order', 'ProductAddToCart', dimensions, metric_id)
        #print('Current value: ', current_value)
        #new_value = current_value + 1 
        dimensions = [{'Name': 'product_slug', 'Value': item['slug']}]
        put_metric_data('Order', 'AddToCartProduct', 1, 'Count', dimensions)

        end_time = time.time()
        duration = end_time - start_time
        put_metric_data('Order', 'AddToCartDuration', duration*1000, 'Milliseconds', [])

        flash('Item has been added to cart', 'success')
    
    user_name, user_photo = get_user_name_photo()
    return render_template('product.html', product=item, form=form, reviews=reviewslist, 
        user_name = user_name, user_photo=user_photo)


@app.route('/checkout', methods=['GET'])
@xray_recorder.capture('checkout')
def summary():
    start_time = time.time()
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('home'))
    order = OrderClient.get_order()
    print("Summary", order)
    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('home'))

    OrderClient.post_checkout()
    end_time = time.time()
    duration = end_time - start_time
    put_metric_data('Order', 'OrderCheckoutDuration', duration*1000, 'Milliseconds', [])
    return redirect(url_for('thank_you'))

@app.route('/order/thank-you', methods=['GET'])
@xray_recorder.capture('thanks')
def thank_you():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('home'))

    session.pop('order', None)
    flash('Thank you for your order', 'success')
    user_name, user_photo = get_user_name_photo()
    return render_template('thanks.html', user_name = user_name, user_photo=user_photo)

@app.route('/cart', methods=['GET'])
@xray_recorder.capture('cart')
def cart():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    try:
        result = OrderClient.get_cart()
        #print(result)
        products=result['result']
        productsInCart=[]
        totalamount=0
        for p in products:
            resp = ProductClient.get_product(str(p['product_slug']))
            itemdict={}
            itemdict['quantity']=p['quantity']
            itemdict['name']=resp['result']['name']
            itemdict['description']=resp['result']['description']
            itemdict['slug']=resp['result']['slug']
            itemdict['price']=resp['result']['price']
            itemdict['image']=resp['result']['image']
            itemdict['total']=int(p['quantity'])*float(resp['result']['price'])
            totalamount=totalamount+float(itemdict['total'])
            totalamount=round(totalamount,2)
            productsInCart.append(itemdict)

        #print(productsInCart)
    except requests.exceptions.ConnectionError:
        productsInCart=[]
    user_name, user_photo = get_user_name_photo()
    return render_template('cart.html', products=productsInCart, totalamount=totalamount, 
        user_name = user_name, user_photo=user_photo)

@app.route('/orders', methods=['GET'])
@xray_recorder.capture('orders')
def orders():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    try:
        result = OrderClient.get_orders()
        orders=result['result']
        ordersPlaced=[]
        for p in orders:
            print(p)
            itemdict={}
            itemdict['itemscount']=len(p['items'])
            itemdict['date_added']=p['date_added']
            itemdict['id']=p['order_id']
            itemdict['amount']=p['amount']
            itemdict['productimages']=[]

            for q in p['items']:
                resp=ProductClient.get_product(q['product_slug'])
                itemdict['productimages'].append(resp['result']['image'])
                
            ordersPlaced.append(itemdict)
    except:
        ordersPlaced=[]

    user_name, user_photo = get_user_name_photo()
    return render_template('orders.html', orders=ordersPlaced, user_name = user_name, user_photo=user_photo)

@app.route('/postreview', methods=['POST'])
def postreview():
    ratinginput = request.form.get('ratinginput') 
    reviewinput = request.form.get('reviewinput')
    productslug = request.form.get('productslug')
    response = UserClient.get_user()
    user = response['result']
    username = user['username']
    ReviewClient.post_review(username, productslug, ratinginput, reviewinput)
    flash('Thank you for your review', 'success')
    return redirect('/product/'+productslug)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)    
