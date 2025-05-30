from app import db
from datetime import datetime

class Food(db.Model):
    __tablename__ = 'foods'

    # Kolom identifikasi utama
    id = db.Column(db.Integer, primary_key=True)
    food_code = db.Column(db.String(50), unique=True, nullable=True) # Dari kolom 'kode' di CSV

    # Informasi dasar makanan dari CSV
    name = db.Column(db.String(255), nullable=False) # Dari 'nama_makanan' di CSV

    # Energi dan Makronutrien Utama dari CSV
    caloric_value = db.Column(db.Float, nullable=True) # Dari 'energi_kal' di CSV
    protein = db.Column(db.Float, nullable=True) # Dari 'protein_g' di CSV
    fat = db.Column(db.Float, nullable=True) # Dari 'lemak_g' di CSV
    carbohydrates = db.Column(db.Float, nullable=True) # Dari 'karbohidrat_g' di CSV
    dietary_fiber = db.Column(db.Float, nullable=True) # Dari 'serat_g' di CSV

    # Mineral dari CSV
    calcium = db.Column(db.Float, nullable=True) # Dari 'kalsium_mg' di CSV
    phosphorus = db.Column(db.Float, nullable=True) # Dari 'fosfor_mg' di CSV
    iron = db.Column(db.Float, nullable=True) # Dari 'besi_mg' di CSV
    sodium = db.Column(db.Float, nullable=True) # Dari 'natrium_mg' di CSV
    potassium = db.Column(db.Float, nullable=True) # Dari 'kalium_mg' di CSV
    copper = db.Column(db.Float, nullable=True) # Dari 'tembaga_mg' di CSV
    zinc = db.Column(db.Float, nullable=True) # Dari 'seng_mg' di CSV
    
    # Vitamin dari CSV
    retinol_mcg = db.Column(db.Float, nullable=True) # Dari 'retinol_mcg' di CSV
    thiamin_mg = db.Column(db.Float, nullable=True) # Dari 'thiamin_mg' di CSV
    riboflavin_mg = db.Column(db.Float, nullable=True) # Dari 'riboflavin_mg' di CSV
    niacin_mg = db.Column(db.Float, nullable=True) # Dari 'niasin_mg' di CSV
    vitamin_c = db.Column(db.Float, nullable=True) # Dari 'vitamin_c_mg' di CSV
    
    # Informasi Tambahan Kategorikal dari CSV
    food_status = db.Column(db.String(100), nullable=True) # Dari 'status_makanan' di CSV
    food_group = db.Column(db.String(100), nullable=True) # Dari 'kelompok_makanan' di CSV
    meal_type = db.Column(db.String(100), nullable=True) # Dari 'meal_type' di CSV

    # Kolom yang diisi oleh FoodClassifier (logika aplikasi)
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=True) 
    contains_dairy = db.Column(db.Boolean, default=False)
    contains_nuts = db.Column(db.Boolean, default=False) 
    contains_seafood = db.Column(db.Boolean, default=False)
    contains_eggs = db.Column(db.Boolean, default=False)
    contains_soy = db.Column(db.Boolean, default=False)


    # Timestamp (logika aplikasi)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Food {self.name} ({self.food_code})>'

