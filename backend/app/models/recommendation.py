from app import db
from datetime import datetime

class DietGoal(db.Model):
    __tablename__ = 'diet_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_weight = db.Column(db.Float, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    medical_condition = db.Column(db.Enum('none', 'diabetes', 'hypertension', 'obesity'), default='none', server_default='none', nullable=False) # Ditambahkan server_default dan nullable=False
    status = db.Column(db.Enum('active', 'completed', 'abandoned'), default='active', server_default='active', nullable=False) # Ditambahkan server_default dan nullable=False
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('diet_goals', lazy=True))

    def __repr__(self):
        return f'<DietGoal {self.id} for User {self.user_id}>'

class FoodPreference(db.Model):
    __tablename__ = 'food_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Memperbarui Enum untuk mencocokkan dengan opsi di frontend dan kebutuhan klasifikasi
    preference_type = db.Column(db.Enum(
        'vegetarian', 'halal', # Tipe Diet
        'dairy_free', 'nut_free', 'seafood_free', 'egg_free', 'soy_free' # Alergi
    ), nullable=False) # Dibuat nullable=False karena tipe preferensi harus ada
    is_active = db.Column(db.Boolean, default=True, nullable=False) # Dibuat nullable=False
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('food_preferences', lazy=True))

    def __repr__(self):
        return f'<FoodPreference {self.preference_type} for User {self.user_id}>'

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    score = db.Column(db.Float, nullable=True) # Skor dari sistem rekomendasi
    recommendation_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date) # Default ke tanggal hari ini
    
    # Feedback Pengguna
    is_consumed = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Integer, nullable=True) # Rating bisa null jika belum diberi
    feedback_date = db.Column(db.DateTime, nullable=True) # Tanggal feedback diberikan
    
    # Klasifikasi dari ML (hanya meal_type sekarang)
    meal_type = db.Column(db.String(50), nullable=True) # Misal: 'Sarapan', 'Makan Siang', 'Makan Malam', 'Cemilan'
    # food_status dihapus sesuai rencana

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('recommendations', lazy=True))
    food = db.relationship('Food', backref=db.backref('recommendations', lazy=True))

    def __repr__(self):
        return f'<Recommendation {self.id} for User {self.user_id} - Food {self.food_id}>'
