import os
import requests
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import render_template, session, redirect, url_for, flash, request, jsonify
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, user_loaded_from_header 
from passlib.hash import sha256_crypt
import time, random
import avinit
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

app = Flask(__name__, static_folder='static') 
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['WTF_CSRF_SECRET_KEY'] = "sEWQkE9oYBiF5fVJnm278i7"
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_message = "You must be login to access this page."
login_manager.login_view = "login"

bootstrap = Bootstrap()

migrate = Migrate(app, db)


#------------User---------

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
            'photo': '/uploads/'+self.photo,
            'id': self.id,
            'api_key': self.api_key,
            'is_active': True,
            'is_admin': self.is_admin
        }


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        user = User.query.filter_by(api_key=api_key).first()
        if user:
            return user
    return None

@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
    g.login_via_header = True

def get_user():
    if current_user.is_authenticated:
        return current_user.to_json()
    else:
        return {'message': 'Not logged in'}

def get_user_with_id(id):
    item = User.query.filter_by(id=id).first()
    if item is not None:
        response = item.to_json()
    else:
        response = {'message': 'Cannot find user'}
    return response

def get_user_name_photo():
    try:
        user = get_user()
        user_name = user['first_name']+" "+user['last_name']
        user_photo = user['photo']
    except:
        user_name=''
        user_photo=''
    return user_name, user_photo

#------------End User-----

#-------Product---------
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
            'image': "/uploads/"+self.image
        }

def get_product_with_id(id):
    item = Product.query.filter_by(id=id).first()
    if item is not None:
        response = item.to_json()
    else:
        response = {'message': 'Cannot find user'}
    return response

#------End Product----

#---------Order---------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('OrderItem', backref='orderItem')
    is_open = db.Column(db.Boolean, default=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def create(self, user_id):
        self.user_id = user_id
        self.is_open = True
        return self

    def to_json(self):
        items = []
        amount=0
        for i in self.items:
            items.append(i.to_json())
            amount=amount+i.price*i.quantity
            amount=round(amount,2)

        return {
            'id': self.id,
            'items': items,
            'is_open': self.is_open,
            'user_id': self.user_id,
            'date_added': self.date_added.strftime("%b %d, %Y"),
            'amount': amount
        }


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

    def to_json(self):
        return {
            'price': self.price,
            'product': self.product_id,
            'quantity': self.quantity
        }

def get_order():
    user = get_user()
    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    if open_order is None:
        return {'result':False, 'message': 'No order found'}
    else:
        return {'result': open_order.to_json()}

def get_order_from_session():
    default_order = {
        'items': {},
        'total': 0,
    }
    return session.get('order', default_order)

def get_orders():
    user = get_user()
    if not 'id' in user:
        return []

    orders = Order.query.filter_by(user_id=user['id'], is_open=0)

    if orders is None:
        response = []
    else:
        items=[]
        for item in orders:
            items.append(item.to_json())

        response = items
    return response

def post_add_to_cart(product_id, price, qty=1):
    user = get_user()
    p_id = int(product_id)
    qty = int(qty)
    price = float(price)
    u_id = int(user['id'])

    known_order = Order.query.filter_by(user_id=u_id, is_open=1).first()

    if known_order is None:
        known_order = Order()
        known_order.is_open = True
        known_order.user_id = u_id

        order_item = OrderItem(p_id, qty, price)
        known_order.items.append(order_item)
    else:
        found = False

        for item in known_order.items:
            if item.product_id == p_id:
                found = True
                item.quantity += qty

        if found is False:
            order_item = OrderItem(p_id, qty, price)
            known_order.items.append(order_item)

    db.session.add(known_order)
    db.session.commit()
    response = known_order.to_json()
    return response

def post_checkout():
    user = get_user()

    if not 'id' in user:
        return {'message': 'Not logged in'}

    order_model = Order.query.filter_by(user_id=user['id'], is_open=1).first()
    order_model.is_open = 0

    db.session.add(order_model)
    db.session.commit()

    response = order_model.to_json()
    return response
    
   
def get_cart():
    user = get_user()
    if not 'id' in user:
        return []

    open_order = Order.query.filter_by(user_id=user['id'], is_open=1).first()

    if open_order is None:
        response = []
    else:
        items=[]
        for item in open_order.items:
            items.append(item.to_json())

        response = items
    return response
#---------End Order------

#--------Review--------
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer)
    rating = db.Column(db.Float, default=0)
    description = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'rating': self.rating,
            'description': self.description,
            'date_added': self.date_added.strftime("%b %d, %Y")
        }

def post_review(user_id, product_id, rating, description):
    item = Review()
    item.product_id = product_id
    item.user_id = user_id
    item.rating = rating
    item.description=description

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Review added', 'review': item.to_json()})
    return response

def get_reviews(product_id):
    reviews = Review.query.filter_by(product_id=product_id)
    if reviews is None:
        response = []
    else:
        items=[]
        for item in reviews:
            items.append(item.to_json())

        response = items
    return response

#--------End Review------------


#--------Forms--------------
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

#--------End Forms--------------


#--------Routes--------------

@app.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        session['order'] = get_order_from_session()

    try:
        items = []
        for row in Product.query.all():
            items.append(row.to_json())
        products = {'results': items}
    except requests.exceptions.ConnectionError:
        products = {
            'results': []
        }

    user_name, user_photo = get_user_name_photo()
    return render_template('home.html', products=products, user_name = user_name, user_photo=user_photo)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            username = form.username.data
            item = User.query.filter_by(username=username).first()
            # Search for existing user
            if item is not None:
                # Existing user found
                flash('Please try another username', 'error')
                return render_template('register/index.html', form=form)
            else:
                # Attempt to create new user
                user = False
                first_name = form.first_name.data
                last_name = form.last_name.data
                email = form.email.data
                username = form.username.data
                password = sha256_crypt.hash(form.password.data)

                user = User()
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.password = password
                user.username = username
                user.authenticated = True

                name=first_name+' '+ last_name
                filename = "user"+str(int(time.time()*1000))+".png"
                imgpath=os.path.join(app.config['UPLOAD_FOLDER'], filename)
                r = lambda: random.randint(0,255)
                colors=[]
                colors.append('#%02X%02X%02X' % (r(),r(),r()))
                avinit.get_png_avatar(name, output_file=imgpath, colors=colors)
                user.photo = filename

                db.session.add(user)
                db.session.commit()

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
            username = request.form['username']
            user = User.query.filter_by(username=username).first()
            api_key=None
            if user:
                if sha256_crypt.verify(str(request.form['password']), user.password):
                    user.encode_api_key()
                    db.session.commit()
                    login_user(user)
                    api_key = user.api_key

                if api_key:
                    session['user_api_key'] = api_key
                    userjson = user.to_json()
                    session['user'] = userjson
                    
                    order = get_order()
                    if order['result']:
                        session['order'] = order

                    flash('Welcome back, ' + userjson['first_name'], 'success')
                    return redirect(url_for('home'))
            else:
                flash('Cannot login', 'error')
        else:
            flash('Errors found', 'error')
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        logout_user()
    session.clear()
    return redirect(url_for('home'))

#curl -X POST -F "name=Product 1" -F "slug=product-1" -F "description=This is product 1" -F "price=49.99" -F "image=@product1.jpg" http://localhost:5000/api/product/create
@app.route('/api/product/create', methods=['POST'])
def post_create():
    name = request.form.get('name') 
    slug = request.form.get('slug')
    description = request.form.get('description')
    price = request.form.get('price')
    image = request.files.get('image')

    filename = secure_filename(image.filename)
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    item = Product()
    item.name = name
    item.slug = slug
    item.image = image
    item.price = price
    item.image = filename
    item.description=description

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Product added', 'product': item.to_json()})
    return response


@app.route('/product/<slug>', methods=['GET', 'POST'])
def product(slug):
    product = Product.query.filter_by(slug=slug).first()
    if product is not None:
        item = product.to_json()
        form = ItemForm(product_id=item['id'])
        reviews=get_reviews(item['id'])
        print('**************************')
        print(reviews)
        reviewslist=[]
        for review in reviews:
            try:
                reviewdict={}
                reviewdict['rating']=review['rating']
                reviewdict['description']=review['description']
                reviewdict['date_added']=review['date_added']
                reviewer=get_user_with_id(review['user_id'])
                reviewdict['photo']=reviewer['photo']
                reviewdict['user_name']=reviewer['first_name']+' '+reviewer['last_name']
                reviewslist.append(reviewdict)
            except:
                pass

    if request.method == "POST":
        if 'user' not in session:
            flash('Please login', 'error')
            return redirect(url_for('login'))
        order = post_add_to_cart(product_id=item['id'], price=item['price'], qty=1)
        session['order'] = order
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
    order = get_order()

    if len(order['result']['items']) == 0:
        flash('No order found', 'error')
        return redirect(url_for('home'))

    post_checkout()

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
        products = get_cart()
        productsInCart=[]
        totalamount=0
        for p in products:
            item = Product.query.filter_by(id=str(p['product'])).first()
            resp=item.to_json()
            itemdict={}
            itemdict['quantity']=p['quantity']
            itemdict['name']=resp['name']
            itemdict['description']=resp['description']
            itemdict['id']=resp['id']
            itemdict['slug']=resp['slug']
            itemdict['price']=resp['price']
            itemdict['image']=resp['image']
            itemdict['total']=p['quantity']*resp['price']
            totalamount=totalamount+itemdict['total']
            totalamount=round(totalamount,2)
            productsInCart.append(itemdict)

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
        orders = get_orders()
        ordersPlaced=[]
        for p in orders:
            itemdict={}
            itemdict['itemscount']=len(p['items'])
            itemdict['id']=p['id']
            itemdict['date_added']=p['date_added']
            itemdict['amount']=p['amount']
            itemdict['productimages']=[]

            for q in p['items']:
                resp=get_product_with_id(q['product'])
                itemdict['productimages'].append(resp['image'])

            ordersPlaced.append(itemdict)

    except requests.exceptions.ConnectionError:
        ordersPlaced=[]

    user_name, user_photo = get_user_name_photo()
    return render_template('orders.html', orders=ordersPlaced, user_name = user_name, user_photo=user_photo)

@app.route('/postreview', methods=['POST'])
def postreview():
    ratinginput = request.form.get('ratinginput') 
    reviewinput = request.form.get('reviewinput')
    productslug = request.form.get('productslug')
    user = get_user()
    user_id = int(user['id'])
    product_id = request.form.get('productid')
    post_review(user_id, product_id, ratinginput, reviewinput)
    flash('Thank you for your review', 'success')
    return redirect('/product/'+productslug)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)    