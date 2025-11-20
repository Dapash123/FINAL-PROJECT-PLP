from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # farmer, supplier, ngo, logistics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FoodListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo_url = db.Column(db.String(255))
    description = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.String(50))
    shelf_life = db.Column(db.String(50))
    status = db.Column(db.String(20), default='available')  # available, matched, picked_up
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('food_listings', lazy=True))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('food_listing.id'), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    food = db.relationship('FoodListing', backref=db.backref('matches', lazy=True))
    partner = db.relationship('User', backref=db.backref('matches', lazy=True))

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    supplier = db.relationship('User', backref=db.backref('payments', lazy=True))
