from app import db
from datetime import datetime


class Food(db.Model):
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    caloric_value = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbohydrates = db.Column(db.Float)
    fat = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    
    # Dietary Categories
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=True)
    
    # Allergen Information
    contains_dairy = db.Column(db.Boolean, default=False)
    contains_nuts = db.Column(db.Boolean, default=False)
    contains_seafood = db.Column(db.Boolean, default=False)
    contains_eggs = db.Column(db.Boolean, default=False)
    contains_soy = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)