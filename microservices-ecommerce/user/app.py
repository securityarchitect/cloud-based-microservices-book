import os
from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_migrate import Migrate
from flask.sessions import SecureCookieSessionInterface
from flask import g
from flask_sqlalchemy import SQLAlchemy
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

class CustomSessionInterface(SecureCookieSessionInterface):
    """Prevent creating session from API requests."""
    def save_session(self, *args, **kwargs):
        if g.get('login_via_header'):
            return
        return super(CustomSessionInterface, self).save_session(*args, **kwargs)

db = SQLAlchemy()
login_manager = LoginManager()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///' + os.path.join(basedir, 'user.sqlite')
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
login_manager.init_app(app)

migrate = Migrate(app, db)
app.session_interface = CustomSessionInterface()


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
            'photo': self.photo,
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


@app.route('/api/users', methods=['GET'])
def get_users():
    data = []
    for row in User.query.all():
        data.append(row.to_json())

    response = jsonify(data)
    return response

@app.route('/api/user/create', methods=['POST'])
def post_register():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    username = request.form['username']

    password = sha256_crypt.hash((str(request.form['password'])))

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

    response = jsonify({'message': 'User added', 'result': user.to_json()})

    return response


@app.route('/api/user/login', methods=['POST'])
def post_login():
    username = request.form['username']
    user = User.query.filter_by(username=username).first()
    if user:
        if sha256_crypt.verify(str(request.form['password']), user.password):
            user.encode_api_key()
            db.session.commit()
            login_user(user)

            return make_response(jsonify({'message': 'Logged in', 'api_key': user.api_key}))

    return make_response(jsonify({'message': 'Not logged in'}), 401)


@app.route('/api/user/logout', methods=['POST'])
def post_logout():
    if current_user.is_authenticated:
        logout_user()
        return make_response(jsonify({'message': 'You are logged out'}))
    return make_response(jsonify({'message': 'You are not logged in'}))


@app.route('/api/user/<username>/exists', methods=['GET'])
def get_username(username):
    item = User.query.filter_by(username=username).first()
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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@user_loaded_from_header.connect
def user_loaded_from_header(self, user=None):
    g.login_via_header = True


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)