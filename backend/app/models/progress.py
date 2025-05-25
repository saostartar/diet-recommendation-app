from app import db
from datetime import datetime

class WeightProgress(db.Model):
    __tablename__ = 'weight_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('weight_progress', lazy=True))
    
    # Method to get weight difference from previous record
    def get_weight_difference(self):
        previous = WeightProgress.query.filter(
            WeightProgress.user_id == self.user_id,
            WeightProgress.date < self.date
        ).order_by(WeightProgress.date.desc()).first()
        
        if previous:
            return self.weight - previous.weight
        return 0