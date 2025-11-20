from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from models import db, User, FoodListing, Match
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)

# Use SQLite for local development
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///harvesthub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    if not all([name, email, password, role]):
        return jsonify({'message': 'Missing required fields'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 409
    hashed_pw = generate_password_hash(password)
    user = User(name=name, email=email, password=hashed_pw, role=role)
    db.session.add(user)
    db.session.commit()
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        },
        'token': token
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'message': 'Missing email or password'}), 400
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        },
        'token': token
    }), 200

@app.route('/profile', methods=['GET'])
@token_required
def profile(current_user):
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role
    })

@app.route('/food', methods=['POST'])
@token_required
def add_food(current_user):
    if 'photo' in request.files:
        photo = request.files['photo']
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        photo_url = f'/uploads/{filename}'
    else:
        photo_url = None
    description = request.form.get('description')
    location = request.form.get('location')
    quantity = request.form.get('quantity')
    shelf_life = request.form.get('shelf_life')
    if not all([description, location]):
        return jsonify({'message': 'Missing required fields'}), 400
    food = FoodListing(
        user_id=current_user.id,
        photo_url=photo_url,
        description=description,
        location=location,
        quantity=quantity,
        shelf_life=shelf_life
    )
    db.session.add(food)
    db.session.commit()
    return jsonify({'message': 'Food listing added!'}), 201

@app.route('/food', methods=['GET'])
@token_required
def get_food(current_user):
    food_list = FoodListing.query.order_by(FoodListing.created_at.desc()).all()
    result = []
    for food in food_list:
        poster = User.query.get(food.user_id)
        result.append({
            'id': food.id,
            'photo_url': food.photo_url,
            'description': food.description,
            'location': food.location,
            'quantity': food.quantity,
            'shelf_life': food.shelf_life,
            'status': food.status,
            'poster_name': poster.name if poster else 'Unknown'
        })
    return jsonify({'food': result})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/match', methods=['POST'])
@token_required
def claim_food(current_user):
    data = request.get_json()
    food_id = data.get('food_id')
    if not food_id:
        return jsonify({'message': 'Missing food_id'}), 400
    food = FoodListing.query.get(food_id)
    if not food or food.status != 'available':
        return jsonify({'message': 'Food not available'}), 404
    match = Match(food_id=food.id, partner_id=current_user.id, status='pending')
    food.status = 'matched'
    db.session.add(match)
    db.session.commit()
    return jsonify({'message': 'Food claimed!'}), 200

@app.route('/')
def index():
    return {'message': 'Welcome to HarvestHub API!'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
