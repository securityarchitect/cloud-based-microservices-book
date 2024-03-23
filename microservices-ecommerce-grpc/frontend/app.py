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
from flask_login import LoginManager, UserMixin
from flask_login import current_user, login_user, logout_user, login_required
from flask import session, request
from werkzeug.utils import secure_filename
import grpc
import product_pb2
import product_pb2_grpc
import review_pb2
import review_pb2_grpc
import order_pb2
import order_pb2_grpc
import user_pb2
import user_pb2_grpc
import boto3
import time
import json
import avinit
import random

login_manager = LoginManager()
bootstrap = Bootstrap()

app = Flask(__name__, static_folder='static') 
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['WTF_CSRF_SECRET_KEY'] = "sEWQkE9oYBiF5fVJnm278i7"
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['BUCKET_NAME'] = 'microservices-ecommerce-app'
app.config['CLOUDFRONT_URL'] = 'https://dn2aztcn1xe1u.cloudfront.net'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['AWS_ACCESS_KEY'] = 'AKIATHISISANEXAMPLEKEY'
app.config['AWS_SECRET_KEY'] = 'APthisisanexamplesecretkey'

USER_SERVICE_URL='localhost:50054'
PRODUCT_SERVICE_URL='localhost:50051'
ORDER_SERVICE_URL='localhost:50053'
REVIEW_SERVICE_URL='localhost:50052'

login_manager.init_app(app)
login_manager.login_message = "Please login"
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data.get('id')
  
    def get_id(self):
        return self.id 


class UserClient:
    def __init__(self):
        # Create gRPC channel
        self.channel = grpc.insecure_channel(USER_SERVICE_URL)
        # Create stub
        self.stub = user_pb2_grpc.UserServiceStub(self.channel)

    def post_login(self, username, password):
        request = user_pb2.LoginRequest(username=username, password=password)
        response = self.stub.LoginUser(request)
        try:
            userdic = {
            'id': response.id,
            'first_name': response.first_name,
            'last_name': response.last_name,
            'username': response.username,
            'email': response.email,
            'photo': response.photo,
            'is_admin': response.is_admin,
            'api_key': response.api_key
            }
            print(userdic)
        except:
            userdic={}
            userdic['api_key']=False
        return userdic

    def get_user(self, user_id):
        request = user_pb2.GetUserRequest(id=user_id)
        response = self.stub.GetUserById(request)
        userdic = {
            'id': response.id,
            'first_name': response.first_name,
            'last_name': response.last_name,
            'username': response.username,
            'email': response.email,
            'photo': response.photo,
            'is_admin': response.is_admin,
            'api_key': response.api_key
            }
        return userdic


    def post_user_create(self, first_name, last_name, username, email, password, photo):
        request = user_pb2.CreateUserRequest(first_name=first_name, last_name=last_name, username=username, email=email, password=password, photo=photo)
        response = self.stub.CreateUser(request)

        userdic = {
            'id': response.id,
            'first_name': response.first_name,
            'last_name': response.last_name,
            'username': response.username,
            'email': response.email,
            'photo': response.photo,
            'is_admin': response.is_admin,
            'api_key': response.api_key
            }
        return userdic

    def does_exist(self, username):
        request = user_pb2.UsernameRequest(username=username)
        response = self.stub.CheckUsername(request)
        return response.result

class ProductClient:
    def __init__(self):
        # Create gRPC channel
        self.channel = grpc.insecure_channel(PRODUCT_SERVICE_URL)
        # Create stub
        self.stub = product_pb2_grpc.ProductServiceStub(self.channel)

    def get_products(self):
        request = product_pb2.Empty()
        response = self.stub.GetProducts(request)
        # Convert response to list
        products = []
        for p in response.products:
            product = {
            'id': p.id,
            'name': p.name,
            'price': round(p.price,2),
            'description': p.description,
            'slug': p.slug,
            'image': p.image
            }
            products.append(product)
        
        productsdic={}
        productsdic['results']=products
        return productsdic

    def get_product(self, slug):
        request = product_pb2.ProductRequest(slug=slug)
        response = self.stub.GetProduct(request)
        product = {
            'id': response.id,
            'name': response.name,
            'price': round(response.price,2),
            'description': response.description,
            'slug': response.slug,
            'image': response.image
            }
        productsdic={}
        productsdic['result']=product
        return productsdic

    def get_product_with_id(self, pid):
        request = product_pb2.ProductRequestID(id=pid)
        response = self.stub.GetProductWithID(request)
        product = {
            'id': response.id,
            'name': response.name,
            'description': response.description,
            'slug': response.slug,
            'price': round(response.price,2),
            'image': response.image
            }
        productsdic={}
        productsdic['result']=product
        return productsdic
    
    def create_product(self, name, description, slug, price, uploadedFileURL):
        request = product_pb2.ProductCreateRequest(name=name, description=description, slug=slug, price=price, image=uploadedFileURL)
        response = self.stub.CreateProduct(request)
        product = {
            'id': response.id,
            'name': response.name,
            'price': round(response.price,2),
            'description': response.description,
            'slug': response.slug,
            'image': response.image
            }
        productsdic={}
        productsdic['result']=product
        return productsdic


class OrderClient:
    def __init__(self):
        # Create gRPC channel
        self.channel = grpc.insecure_channel(ORDER_SERVICE_URL)
        # Create stub
        self.stub = order_pb2_grpc.OrderServiceStub(self.channel)

    def get_order(self, user_id):
        request = order_pb2.GetOrderRequest(user_id=user_id)
        response = self.stub.GetOrder(request)
        orderdic={}
        try:
            order = {
                'id': response.id,
                'items': json.loads(response.items),
                'is_open': response.is_open,
                'user_id': response.user_id,
                'date_added': response.date_added,
                'amount': round(response.amount,2)
            }
        except:
            order={}
        orderdic['result']=order
        return orderdic

    def get_orders(self, user_id):
        request = order_pb2.GetOrdersRequest(user_id=user_id)
        response = self.stub.GetOrders(request)
        # Convert response to list
        orders = []
        for p in response.orders:
            product = {
                'id': p.id,
                'items': json.loads(p.items),
                'is_open': p.is_open,
                'user_id': p.user_id,
                'date_added': p.date_added,
                'amount': round(p.amount,2)
            }
            orders.append(product)
        
        ordersdic={}
        ordersdic['result']=orders
        return ordersdic

    def get_cart(self, user_id):
        request = order_pb2.GetCartRequest(user_id=user_id)
        response = self.stub.GetCart(request)
        items=json.loads(response.items)
        ordersdic={}
        ordersdic['result']=items
        return ordersdic
    
    def post_add_to_cart(self, user_id, product_id, price, qty=1):
        request = order_pb2.AddItemRequest(user_id=user_id, product_id=product_id, qty=qty, price=qty)
        response = self.stub.AddItem(request)

        order = {
            'id': response.id,
            'items': json.loads(response.items),
            'is_open': response.is_open,
            'user_id': response.user_id,
            'date_added': response.date_added,
            'amount': round(response.amount,2)
        }
        orderdic={}
        orderdic['result']=order
        return orderdic

    def post_checkout(self, user_id):
        request = order_pb2.CheckoutRequest(user_id=user_id)
        response = self.stub.Checkout(request)

        order = {
            'id': response.id,
            'items': json.loads(response.items),
            'is_open': response.is_open,
            'user_id': response.user_id,
            'date_added': response.date_added,
            'amount': round(response.amount,2)
        }
        orderdic={}
        orderdic['result']=order
        return orderdic


class ReviewClient:
    def __init__(self):
        # Create gRPC channel
        self.channel = grpc.insecure_channel(REVIEW_SERVICE_URL)
        # Create stub
        self.stub = review_pb2_grpc.ReviewServiceStub(self.channel)

    
    def get_reviews(self, product_id):
        request = review_pb2.GetReviewsRequest(product_id=product_id)
        response = self.stub.GetReviews(request)
        # Convert response to list
        reviews = []
        for p in response.reviews:
            review = {
                'id': p.id,
                'user_id': p.user_id,
                'product_id':p.product_id,
                'rating': p.rating,
                'date_added': p.date_added,
                'description': p.description
            }
            reviews.append(review)
        
        reviewsdic={}
        reviewsdic['result']=reviews
        return reviewsdic


    def post_review(self, user_id, product_id, rating, description):
        request = review_pb2.ReviewRequest(user_id=int(user_id), product_id=int(product_id), rating=float(rating), description=description)
        response = self.stub.AddReview(request)
        review = {
            'id': response.id,
            'user_id': response.user_id,
            'product_id': response.product_id,
            'rating': response.rating,
            'description': response.description,
            'date_added': response.date_added
            }
        reviewdic={}
        reviewdic['result']=review
        return reviewdic


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
    print('Loading user with ID', user_id)
    userclient=UserClient()
    user=userclient.get_user(user_id)
    return User(user)


def get_user_name_photo():
    try:
        user_name = session['user']['first_name']+" "+session['user']['last_name']
        user_photo = session['user']['photo']
    except:
        user_name=''
        user_photo=''
        
    return user_name, user_photo

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


@app.route('/', methods=['GET'])
def home():
    print('Home----')
    print(current_user)
    if current_user.is_authenticated:
        user_id=session['user']['id']
        orderclient=OrderClient()
        order = orderclient.get_order(user_id)
        session['order'] = order['result'] 
        
    try:
        productclient = ProductClient()
        products = productclient.get_products()
    except requests.exceptions.ConnectionError:
        products = {
            'results': []
        }

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
            userclient=UserClient()
            exist = userclient.does_exist(username)
            if exist:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create new user
                name=form.first_name.data+' '+ form.last_name.data
                filename = "user"+str(int(time.time()*1000))+".png"
                imgpath=os.path.join(app.config['UPLOAD_FOLDER'], filename)
                r = lambda: random.randint(0,255)
                colors=[]
                colors.append('#%02X%02X%02X' % (r(),r(),r()))
                avinit.get_png_avatar(name, output_file=imgpath, colors=colors)

                uploadedFileURL = s3uploading(filename)
                
                user = userclient.post_user_create(form.first_name.data, form.last_name.data, 
                                form.username.data, form.email.data, form.password.data, uploadedFileURL)
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
            userclient=UserClient()
            user = userclient.post_login(form.username.data, form.password.data)
            if user['api_key']:
                loginuser = User(user)
                print('Login user---')
                print(loginuser)
                print(user)
                login_user(loginuser)
                print(current_user)
                print(current_user.is_authenticated)
                session['user_api_key'] = user['api_key']
                sessiondict={}
                sessiondict['first_name'] = user['first_name']
                sessiondict['last_name'] = user['last_name']
                sessiondict['id'] = user['id']
                sessiondict['username'] = user['username']
                sessiondict['email'] = user['email']
                sessiondict['api_key'] = user['api_key']
                sessiondict['photo'] = user['photo']
                session['user'] = sessiondict
                user_id=session['user']['id']

                flash('Welcome back, ' + user['first_name'], 'success')
                return redirect(url_for('home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        session.clear()
        logout_user()
    return redirect(url_for('home'))


@app.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):
    productclient = ProductClient()
    response = productclient.get_product(slug)
    item = response['result']
    form = ItemForm(product_id=item['id'])
    reviewslist=[]

    reviewclient=ReviewClient()
    result=reviewclient.get_reviews(item['id'])
    reviews=result['result']
    
    user_id=session['user']['id']

    for review in reviews:
        try:
            reviewdict={}
            reviewdict['rating']=review['rating']
            reviewdict['description']=review['description']
            reviewdict['date_added']=review['date_added']
            userclient = UserClient()
            reviewer = userclient.get_user(review['user_id'])
            reviewdict['photo']=reviewer['photo']
            reviewdict['user_name']=reviewer['first_name']+' '+reviewer['last_name']
            reviewslist.append(reviewdict)
        except:
            pass

    if request.method == "POST":
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('login'))
        
        print('Adding to cart for user: ', user_id)
        orderclient=OrderClient()
        order = orderclient.post_add_to_cart(user_id, product_id=item['id'], price=item['price'], qty=1)
        session['order'] = order['result']
        flash('Item has been added to cart', 'success')
    
    user_name, user_photo = get_user_name_photo()
    return render_template('product.html', product=item, form=form, reviews=reviewslist, 
        user_name = user_name, user_photo=user_photo)


@app.route('/checkout', methods=['GET'])
def summary():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('home'))
    
    user_id=session['user']['id']
    orderclient=OrderClient()
    order = orderclient.get_order(user_id)

    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('home'))

    orderclient=OrderClient()
    orderclient.post_checkout(user_id)

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
    user_id=session['user']['id']
    user_name, user_photo = get_user_name_photo()
    return render_template('thanks.html', user_name = user_name, user_photo=user_photo)

@app.route('/cart', methods=['GET'])
def cart():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    try:
        user_id=session['user']['id']
        print('Getting cart for user: ', user_id)
        orderclient=OrderClient()
        result = orderclient.get_cart(user_id)
        #print(result)
        products=result['result']
        productsInCart=[]
        totalamount=0
        for p in products:
            productclient = ProductClient()
            resp = productclient.get_product_with_id(p['product'])
            itemdict={}
            itemdict['quantity']=p['quantity']
            itemdict['name']=resp['result']['name']
            itemdict['description']=resp['result']['description']
            itemdict['id']=resp['result']['id']
            itemdict['slug']=resp['result']['slug']
            itemdict['price']=resp['result']['price']
            itemdict['image']=resp['result']['image']
            itemdict['total']=p['quantity']*resp['result']['price']
            totalamount=totalamount+itemdict['total']
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
        user_id=session['user']['id']
        print('Getting orders for user: ', user_id)
        orderclient=OrderClient()
        result = orderclient.get_orders(user_id)
        #print(result)
        orders=result['result']
        ordersPlaced=[]
        for p in orders:
            print(p)
            itemdict={}
            itemdict['itemscount']=len(p['items'])
            itemdict['id']=p['id']
            itemdict['date_added']=p['date_added']
            itemdict['amount']=p['amount']
            itemdict['productimages']=[]

            for q in p['items']:
                productclient = ProductClient()
                resp=productclient.get_product_with_id(q['product'])
                itemdict['productimages'].append(resp['result']['image'])
                
            ordersPlaced.append(itemdict)

        #print(ordersPlaced)

    except requests.exceptions.ConnectionError:
        ordersPlaced=[]

    user_name, user_photo = get_user_name_photo()
    return render_template('orders.html', orders=ordersPlaced, user_name = user_name, user_photo=user_photo)

@app.route('/postreview', methods=['POST'])
def postreview():
    ratinginput = request.form.get('ratinginput') 
    reviewinput = request.form.get('reviewinput')
    productslug = request.form.get('productslug')
    user_id = session['user']['id']
    product_id = request.form.get('productid')
    reviewclient = ReviewClient()
    response = reviewclient.post_review(user_id, product_id, ratinginput, reviewinput)
    flash('Thank you for your review', 'success')
    return redirect('/product/'+productslug)


#curl -X POST -F "name=Product 1" -F "slug=product-1" -F "description=This is product 1" -F "price=49.99" -F "image=@product1.jpg" http://localhost:5000/api/product/create
@app.route('/api/product/create', methods=['POST'])
def post_create():
    name = request.form.get('name') 
    slug = request.form.get('slug')
    description = request.form.get('description')
    price = request.form.get('price')
    price = round(float(price), 2) 

    image = request.files.get('image')
    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    uploadedFileURL = s3uploading(filename)
    productclient = ProductClient()
    #pid=int(time.time())-1700000000
    product = productclient.create_product(name, description, slug, price, uploadedFileURL)

    response = jsonify({'message': 'Product added', 'product': product})
    return response



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)    
