import os
from flask import Flask, send_from_directory
from flask_migrate import Migrate
from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = "DoWgTDq87Kmne3TsCjNFabP"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = "development"
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///' + os.path.join(basedir, 'review.sqlite')
app.config['SQLALCHEMY_ECHO'] = True
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
migrate = Migrate(app, db)

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

@app.route('/api/review/add', methods=['POST'])
def post_create():
    user_id = request.form.get('user_id') 
    product_id = request.form.get('product_id') 
    rating = request.form.get('rating')
    description = request.form.get('review')
    
    item = Review()
    item.product_id = product_id
    item.user_id = user_id
    item.rating = rating
    item.description=description

    db.session.add(item)
    db.session.commit()

    response = jsonify({'message': 'Review added', 'review': item.to_json()})
    return response


@app.route('/api/reviews/<productid>', methods=['GET'])
def reviews(productid):
    reviews = Review.query.filter_by(product_id=productid)

    if reviews is None:
        response = jsonify({'message': 'No reviews found', 'result': []})
    else:
        items=[]
        for item in reviews:
            items.append(item.to_json())

        response = jsonify({'result': items})
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
