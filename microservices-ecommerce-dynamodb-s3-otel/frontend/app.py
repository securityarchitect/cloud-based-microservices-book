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
import logging
import boto3

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
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.context import get_current
from opentelemetry import propagators
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

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


USER_SERVICE_URL='http://localhost:5001'
PRODUCT_SERVICE_URL='http://localhost:5002'
ORDER_SERVICE_URL='http://localhost:5003'
REVIEW_SERVICE_URL='http://localhost:5004'

login_manager.init_app(app)
login_manager.login_message = "Please login"
login_manager.login_view = "login"

service_name = 'ecommerce-frontend'
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
tracer = trace.get_tracer('ecommerce-frontend')

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
        with tracer.start_as_current_span("api1_span") as span:
            ctx = baggage.set_baggage("user", json.dumps(session['user']))
            headers = {}
            W3CBaggagePropagator().inject(headers, ctx)
            TraceContextTextMapPropagator().inject(headers, ctx)
            print(headers)
            headers['Authorization'] = 'Basic ' + session['user_api_key']
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


def get_user_name_photo():
    with tracer.start_as_current_span('get_user_name_photo') as span:
        try:
            response = UserClient.get_user()
            user = response['result']
            user_name = user['first_name']+" "+user['last_name']
            user_photo = user['photo']
            ctx = baggage.set_baggage("username", user_name)
        except:
            user_name=''
            user_photo=''
            
        return user_name, user_photo

@app.route('/', methods=['GET'])
def home():
    with tracer.start_as_current_span('home_page') as span:    
        if current_user.is_authenticated:
            session['order'] = OrderClient.get_order_from_session()
        
        try:
            products = ProductClient.get_products()
        except:
            products = {
                'results': []
            }

        span = trace.get_current_span()
        #span.set_attribute(SpanAttributes.HTTP_METHOD, 'GET')
        #span.set_attribute(SpanAttributes.HTTP_URL, url)
        #span.set_attribute('span.kind', trace.SpanKind.CLIENT)
        
        if 'user' in session:
            print(session['user'])
            span.add_event(json.dumps({'event': 'home_page', 'value': session['user']}))  
            span.set_attribute('user', session['user']['username']) 
            span.set_status(Status(status_code=StatusCode.OK))
            ctx = get_current()
        
            #ctx = baggage.set_baggage('user', 'testing', context=ctx)
            #carrier = {}
            #TraceContextTextMapPropagator().inject(carrier)
            propagator = W3CBaggagePropagator()

            #ctx = baggage.set_baggage("Test1", "value1")
            ctx = baggage.set_baggage("test2", "value2", context=ctx)


            #propagator.inject(carrier, ctx)
            output = {}
            propagator.inject(output, context=ctx)
            print(output.get("baggage"))
            #ctx_propagated = propagator.extract(carrier)

            #print(baggage.get_baggage("Test1", context=ctx_propagated))
            #print(baggage.get_baggage("test2", context=ctx_propagated))
            #print('Context', ctx_propagated)
            #print('Carrier', carrier)

        user_name, user_photo = get_user_name_photo()
        return render_template('home.html', products=products, user_name = user_name, 
            user_photo=user_photo)

@app.route('/register', methods=['GET', 'POST'])
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
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == "POST":
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
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/product/<slug>', methods=['GET', 'POST'])
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
        flash('Item has been added to cart', 'success')
    
    user_name, user_photo = get_user_name_photo()
    return render_template('product.html', product=item, form=form, reviews=reviewslist, 
        user_name = user_name, user_photo=user_photo)


@app.route('/checkout', methods=['GET'])
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
    return redirect(url_for('thank_you'))

@app.route('/order/thank-you', methods=['GET'])
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
