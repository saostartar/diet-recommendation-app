from app import db
from datetime import datetime

class DietGoal(db.Model):
    __tablename__ = 'diet_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_weight = db.Column(db.Float, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    medical_condition = db.Column(db.Enum('none', 'diabetes', 'hypertension', 'obesity'), default='none')
    status = db.Column(db.Enum('active', 'completed', 'abandoned'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FoodPreference(db.Model):
    __tablename__ = 'food_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    preference_type = db.Column(db.Enum('vegetarian', 'halal', 'dairy_free', 'nut_free', 'seafood_free', 'egg_free', 'soy_free'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    score = db.Column(db.Float)
    recommendation_date = db.Column(db.Date, nullable=False)
    is_consumed = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer)
    feedback_date = db.Column(db.DateTime)
    food_status = db.Column(db.String(20)) 
    meal_type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)