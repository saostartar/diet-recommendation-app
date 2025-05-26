from app import db
from datetime import datetime

class Food(db.Model):
    __tablename__ = 'foods'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False) # 'Menu' in CSV

    # Macronutrients and Energy
    energy_kj = db.Column(db.Float) # 'Energy (kJ)' in CSV
    caloric_value = db.Column(db.Float) # Akan dikonversi dari energy_kj
    protein = db.Column(db.Float) # 'Protein (g)' in CSV
    fat = db.Column(db.Float) # 'Fat (g)' in CSV
    carbohydrates = db.Column(db.Float) # 'Carbohydrates (g)' in CSV
    dietary_fiber = db.Column(db.Float) # 'Dietary Fiber (g)' in CSV
    
    # Detailed Fats and Cholesterol
    pufa = db.Column(db.Float) # 'PUFA (g)' in CSV - Polyunsaturated Fatty Acids
    cholesterol = db.Column(db.Float) # 'Cholesterol (mg)' in CSV

    # Vitamins
    vitamin_a = db.Column(db.Float) # 'Vitamin A (mg)' in CSV
    vitamin_e = db.Column(db.Float) # 'Vitamin E (eq.) (mg)' in CSV
    vitamin_b1 = db.Column(db.Float) # 'Vitamin B1 (mg)' in CSV
    vitamin_b2 = db.Column(db.Float) # 'Vitamin B2 (mg)' in CSV
    vitamin_b6 = db.Column(db.Float) # 'Vitamin B6 (mg)' in CSV
    total_folic_acid = db.Column(db.Float) # 'Total Folic Acid (µg)' in CSV
    vitamin_c = db.Column(db.Float) # 'Vitamin C (mg)' in CSV

    # Minerals
    sodium = db.Column(db.Float) # 'Sodium (mg)' in CSV
    potassium = db.Column(db.Float) # 'Potassium (mg)' in CSV
    calcium = db.Column(db.Float) # 'Calcium (mg)' in CSV
    magnesium = db.Column(db.Float) # 'Magnesium (mg)' in CSV
    phosphorus = db.Column(db.Float) # 'Phosphorus (mg)' in CSV
    iron = db.Column(db.Float) # 'Iron (mg)' in CSV
    zinc = db.Column(db.Float) # 'Zinc (mg)' in CSV
    
    # Kolom-kolom ini akan diisi oleh FoodClassifier
    is_vegetarian = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=True) # Default ke True, kecuali diklasifikasikan lain
    
    contains_dairy = db.Column(db.Boolean, default=False)
    contains_nuts = db.Column(db.Boolean, default=False) # Mengganti contains_peanuts
    contains_seafood = db.Column(db.Boolean, default=False)
    contains_eggs = db.Column(db.Boolean, default=False)
    contains_soy = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Food {self.name}>'

