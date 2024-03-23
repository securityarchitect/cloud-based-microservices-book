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

login_manager = LoginManager()
bootstrap = Bootstrap()

app = Flask(__name__, static_folder='static') 
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['WTF_CSRF_SECRET_KEY'] = "sEWQkE9oYBiF5fVJnm278i7"
app.config['ENV'] = "development"
app.config['DEBUG'] = True

USER_SERVICE_URL='http://localhost:5001'
PRODUCT_SERVICE_URL='http://localhost:5002'
ORDER_SERVICE_URL='http://localhost:5003'
REVIEW_SERVICE_URL='http://localhost:5004'

login_manager.init_app(app)
login_manager.login_message = "Please login"
login_manager.login_view = "login"

class UserClient:
    @staticmethod
    def post_login(form):
        api_key = False
        payload = {
            'username': form.username.data,
            'password': form.password.data
        }
        url = USER_SERVICE_URL+'/api/user/login'
        response = requests.request("POST", url=url, data=payload)
        if response:
            d = response.json()
            print("This is response from user api: " + str(d))
            if d['api_key'] is not None:
                api_key = d['api_key']
        return api_key

    @staticmethod
    def get_user():

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = USER_SERVICE_URL+'/api/user'
        response = requests.request(method="GET", url=url, headers=headers)
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
        response = requests.request("POST", url=url, data=payload)
        if response:
            user = response.json()
        return user

    @staticmethod
    def does_exist(username):
        url = USER_SERVICE_URL+'/api/user/' + username + '/exists'
        response = requests.request("GET", url=url)
        return response.status_code == 200

class ProductClient:

    @staticmethod
    def get_products():
        r = requests.get(PRODUCT_SERVICE_URL+'/api/products')
        products = r.json()
        return products

    @staticmethod
    def get_product(slug):
        response = requests.request(method="GET", url=PRODUCT_SERVICE_URL+'/api/product/' + slug)
        product = response.json()
        return product

    @staticmethod
    def get_product_with_id(id):
        response = requests.request(method="GET", url=PRODUCT_SERVICE_URL+'/api/productid/' + id)
        product = response.json()
        return product


class OrderClient:
    @staticmethod
    def get_order():
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        url = ORDER_SERVICE_URL+'/api/order'
        response = requests.request(method="GET", url=url, headers=headers)
        order = response.json()
        return order

    @staticmethod
    def post_add_to_cart(product_id, price, image, qty=1):
        payload = {
            'product_id': product_id,
            'qty': qty,
            'price': price,
            'image': image
        }
        url = ORDER_SERVICE_URL+'/api/order/add-item'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, data=payload, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def post_checkout():
        url = ORDER_SERVICE_URL+'/api/order/checkout'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, headers=headers)
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
    def post_review(user_id, product_id, rating, review, user_name, user_photo):
        payload = {
            'user_id': user_id,
            'product_id': product_id,
            'rating': rating,
            'review': review,
            'user_name': user_name,
            'user_photo': user_photo
        }
        url = REVIEW_SERVICE_URL+'/api/review/add'

        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        response = requests.request("POST", url=url, data=payload, headers=headers)
        if response:
            order = response.json()
            return order

    @staticmethod
    def get_reviews(product_id):
        headers = {
            'Authorization': 'Basic ' + session['user_api_key']
        }
        r = requests.get(REVIEW_SERVICE_URL+'/api/reviews/'+str(product_id), headers=headers)
        orders = r.json()
        return orders


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


class OrderItemForm(FlaskForm):
    product_id = HiddenField(validators=[DataRequired()])
    quantity = IntegerField(validators=[DataRequired()])
    order_id = HiddenField()
    submit = SubmitField('Update')


class ItemForm(FlaskForm):
    product_id = HiddenField(validators=[DataRequired()])
    quantity = HiddenField(validators=[DataRequired()], default=1)


@login_manager.user_loader
def load_user(user_id):
    return None

def get_user_name_photo():
    try:
        response = UserClient.get_user()
        user = response['result']
        #user_id = int(user['id'])
        user_name = user['first_name']+" "+user['last_name']
        user_photo = USER_SERVICE_URL+"/uploads/"+user['photo']
    except:
        user_name=''
        user_photo=''
        
    return user_name, user_photo

@app.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        session['order'] = OrderClient.get_order_from_session()

    try:
        products = ProductClient.get_products()
    except requests.exceptions.ConnectionError:
        products = {
            'results': []
        }

    product_service_upload_url = PRODUCT_SERVICE_URL+"/uploads/"
    user_name, user_photo = get_user_name_photo()
    return render_template('home.html', products=products, user_name = user_name, 
        user_photo=user_photo, product_service_upload_url=product_service_upload_url)


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
            api_key = UserClient.post_login(form)
            if api_key:
                session['user_api_key'] = api_key
                user = UserClient.get_user()
                session['user'] = user['result']

                order = OrderClient.get_order()
                if order.get('result', False):
                    session['order'] = order['result']

                flash('Welcome back, ' + user['result']['username'], 'success')
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
    form = ItemForm(product_id=item['id'])

    result=ReviewClient.get_reviews(item['id'])
    reviews=result['result']
    print(reviews)

    if request.method == "POST":
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('login'))
        order = OrderClient.post_add_to_cart(product_id=item['id'], price=item['price'], image=item['image'], qty=1)
        session['order'] = order['result']
        flash('Order has been updated', 'success')
    
    product_service_upload_url = PRODUCT_SERVICE_URL+"/uploads/"
    user_name, user_photo = get_user_name_photo()
    return render_template('product.html', product=item, form=form, reviews=reviews, 
        user_name = user_name, user_photo=user_photo, product_service_upload_url=product_service_upload_url)


@app.route('/checkout', methods=['GET'])
def summary():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    if 'order' not in session:
        flash('No order found', 'error')
        return redirect(url_for('home'))
    order = OrderClient.get_order()

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
        print(result)
        products=result['result']
        productsInCart=[]
        totalamount=0
        for p in products:
            print(p)
            resp = ProductClient.get_product_with_id(str(p['product']))
            print('-----------')
            print(resp)
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

        print(productsInCart)

    except requests.exceptions.ConnectionError:
        productsInCart=[]
    user_name, user_photo = get_user_name_photo()
    return render_template('cart.html', products=productsInCart, totalamount=totalamount, user_name = user_name, user_photo=user_photo)

@app.route('/orders', methods=['GET'])
def orders():
    if 'user' not in session:
        flash('Please login', 'error')
        return redirect(url_for('login'))

    try:
        result = OrderClient.get_orders()
        print(result)
        orders=result['result']
        ordersPlaced=[]
        for p in orders:
            print(p)
            itemdict={}
            itemdict['itemscount']=len(p['items'])
            itemdict['id']=p['id']
            itemdict['date_added']=p['date_added']
            itemdict['amount']=p['amount']
            for q in p['items']:
                if 'productimages' in itemdict:
                    itemdict['productimages'].append(q['image'])
                else:
                    itemdict['productimages']=[]
                    itemdict['productimages'].append(q['image'])
            ordersPlaced.append(itemdict)

        print('********************')
        print(ordersPlaced)

    except requests.exceptions.ConnectionError:
        ordersPlaced=[]

    user_name, user_photo = get_user_name_photo()
    return render_template('orders.html', orders=ordersPlaced, user_name = user_name, user_photo=user_photo)

@app.route('/postreview', methods=['POST'])
def postreview():
    ratinginput = request.form.get('ratinginput') 
    reviewinput = request.form.get('reviewinput')
    productslug = request.form.get('productslug')
    
    #api_key = request.headers.get('Authorization')
    response = UserClient.get_user()
    user = response['result']
    user_id = int(user['id'])
    user_name = user['first_name']+" "+user['last_name']
    user_photo = user['photo']
    product_id = request.form.get('productid')

    print(ratinginput, reviewinput, productslug, user_id, product_id, user_name, user_photo)
    
    ReviewClient.post_review(user_id, product_id, ratinginput, reviewinput, user_name, user_photo)

    return redirect('/product/'+productslug)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)    