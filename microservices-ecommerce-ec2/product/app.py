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

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///' + os.path.join(basedir, 'product.sqlite')
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
        img_path = 'uploads/'+self.image
        img_type = imghdr.what(img_path)
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        if img_type == 'jpeg':
            prefix = 'data:image/jpeg;base64,'
        elif img_type == 'png':
            prefix = 'data:image/png;base64,' 
        img_data = prefix + encoded_string.decode('utf-8') 

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'slug': self.slug,
            'price': self.price,
            'image': img_data
        }

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
