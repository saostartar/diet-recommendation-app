import joblib
import pandas as pd
from typing import Dict, List, Optional
from app.models.user import User
from app.models.recommendation import DietGoal
from app.models.food import Food
import os
import numpy as np

class MLDecisionTreeRecommender:
    """
    Wrapper untuk model Decision Tree yang sudah dilatih.
    Menggantikan atau melengkapi NutritionDecisionTree dengan prediksi ML.
    """
    
    def __init__(self, model_path: str = None):
        """
        Inisialisasi dengan path ke model yang sudah dilatih.
        
        Args:
            model_path: Path ke file model (.joblib)
        """
        self.model = None
        self.model_path = model_path or self._get_default_model_path()
        self.feature_columns = None
        self.is_loaded = False
        
        # Bobot untuk menggabungkan ML score dengan faktor lain
        self.ml_prediction_weight = 0.7  # Bobot untuk prediksi ML
        self.medical_condition_weight = 0.2  # Bobot untuk bonus kondisi medis
        self.diversity_weight = 0.1  # Bobot untuk keragaman
        
    def _get_default_model_path(self) -> str:
        """Mendapatkan path default untuk model."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dataset_dir = os.path.join(script_dir, '..', '..', 'dataset-diet')
        return os.path.join(dataset_dir, 'decision_tree_classifier_v1.joblib')
    
    def load_model(self) -> bool:
        """
        Memuat model Decision Tree yang sudah dilatih.
        
        Returns:
            bool: True jika berhasil dimuat, False jika gagal
        """
        try:
            if not os.path.exists(self.model_path):
                print(f"Model tidak ditemukan di: {self.model_path}")
                return False
                
            self.model = joblib.load(self.model_path)
            self.is_loaded = True
            print(f"Model berhasil dimuat dari: {self.model_path}")
            
            # Dapatkan feature columns dari model training data
            self._set_feature_columns()
            return True
            
        except Exception as e:
            print(f"Error memuat model: {str(e)}")
            self.is_loaded = False
            return False
    
    def _set_feature_columns(self):
        """
        Set kolom fitur yang digunakan untuk prediksi.
        Harus sesuai dengan kolom yang digunakan saat training.
        """
        # Kolom-kolom ini harus sesuai dengan yang digunakan saat generate dataset
        self.feature_columns = [
            # Fitur pengguna
            'user_age', 'user_weight', 'user_height', 'user_bmi',
            
            # Fitur tujuan diet
            'target_weight', 'target_date_days_from_now',
            
            # Fitur kondisi medis (one-hot encoded)
            'medical_condition_diabetes', 'medical_condition_hypertension', 
            'medical_condition_none', 'medical_condition_obesity',
            
            # Fitur preferensi diet (one-hot encoded)
            'diet_preference_halal', 'diet_preference_vegetarian',
            
            # Fitur alergi (one-hot encoded)
            'allergy_dairy_free', 'allergy_egg_free', 'allergy_nut_free', 
            'allergy_seafood_free', 'allergy_soy_free',
            
            # Fitur gender (one-hot encoded)
            'gender_F', 'gender_M',
            
            # Fitur aktivitas (one-hot encoded)
            'activity_active', 'activity_light', 'activity_moderate', 
            'activity_sedentary', 'activity_very_active',
            
            # Fitur makanan
            'food_caloric_value', 'food_protein', 'food_carbohydrates', 
            'food_fat', 'food_dietary_fiber', 'food_sodium', 'food_potassium',
            'food_calcium', 'food_iron', 'food_zinc', 'food_vitamin_c',
            
            # Fitur status makanan (one-hot encoded)
            'food_status_Bahan Dasar', 'food_status_Olahan', 'food_status_Tunggal',
            
            # Fitur grup makanan (one-hot encoded)
            'food_group_Bahan makanan sumber energi', 'food_group_Bahan makanan sumber lemak',
            'food_group_Bahan makanan sumber protein hewani', 'food_group_Bahan makanan sumber protein nabati',
            'food_group_Bahan makanan sumber vitamin dan mineral', 'food_group_Makanan jadi',
            'food_group_Minuman', 'food_group_Rempah dan bumbu',
            
            # Fitur meal type (one-hot encoded)  
            'meal_type_Bahan Dasar', 'meal_type_Cemilan', 'meal_type_Makan Malam',
            'meal_type_Makan Siang', 'meal_type_Sarapan'
        ]
    
    def get_recommendations(
        self,
        user: User,
        goal: DietGoal, 
        preferences: List[str] = None,
        food_ids_to_consider: Optional[List[int]] = None,
        n_recommendations: int = 200
    ) -> List[Dict]:
        """
        Dapatkan rekomendasi menggunakan model Decision Tree yang sudah dilatih.
        
        Args:
            user: Objek pengguna
            goal: Tujuan diet pengguna
            preferences: List preferensi pengguna
            food_ids_to_consider: List ID makanan yang akan dipertimbangkan
            n_recommendations: Jumlah rekomendasi yang diinginkan
            
        Returns:
            List[Dict]: List rekomendasi dengan food_id dan ml_score
        """
        if not self.is_loaded:
            if not self.load_model():
                print("Gagal memuat model, menggunakan fallback scoring")
                return self._get_fallback_recommendations(
                    user, goal, preferences, food_ids_to_consider, n_recommendations
                )
        
        try:
            # Dapatkan makanan yang akan dievaluasi
            foods_to_evaluate = self._get_foods_to_evaluate(food_ids_to_consider)
            
            if not foods_to_evaluate:
                return []
            
            # Buat dataset untuk prediksi
            prediction_data = self._create_prediction_dataset(
                user, goal, preferences or [], foods_to_evaluate
            )
            
            if prediction_data.empty:
                return []
            
            # Lakukan prediksi
            # Model memberikan probabilitas untuk kelas 1 (direkomendasikan)
            probabilities = self.model.predict_proba(prediction_data)[:, 1]
            
            # Buat hasil rekomendasi
            recommendations = []
            for i, food in enumerate(foods_to_evaluate):
                ml_score = float(probabilities[i])
                
                # Tambahkan bonus untuk kondisi medis
                medical_bonus = self._calculate_medical_bonus(food, goal.medical_condition)
                
                # Hitung skor akhir
                final_score = (
                    ml_score * self.ml_prediction_weight +
                    medical_bonus * self.medical_condition_weight
                )
                
                # Pastikan skor dalam rentang [0, 1]
                final_score = max(0, min(1, final_score))
                
                recommendations.append({
                    'food_id': food.id,
                    'ml_score': final_score,
                    'raw_ml_prediction': ml_score,
                    'medical_bonus': medical_bonus
                })
            
            # Urutkan berdasarkan skor dan batasi jumlah
            recommendations.sort(key=lambda x: x['ml_score'], reverse=True)
            return recommendations[:n_recommendations]
            
        except Exception as e:
            print(f"Error dalam prediksi ML: {str(e)}")
            return self._get_fallback_recommendations(
                user, goal, preferences, food_ids_to_consider, n_recommendations
            )
    
    def _get_foods_to_evaluate(self, food_ids_to_consider: Optional[List[int]]) -> List[Food]:
        """Dapatkan makanan yang akan dievaluasi."""
        foods_query = Food.query.filter(
            Food.caloric_value.isnot(None),
            Food.protein.isnot(None),
            Food.carbohydrates.isnot(None),
            Food.fat.isnot(None)
        )
        
        if food_ids_to_consider is not None:
            if not food_ids_to_consider:
                return []
            foods_query = foods_query.filter(Food.id.in_(food_ids_to_consider))
        
        return foods_query.all()
    
    def _create_prediction_dataset(
        self,
        user: User,
        goal: DietGoal,
        preferences: List[str],
        foods: List[Food]
    ) -> pd.DataFrame:
        """
        Buat dataset untuk prediksi dengan format yang sama seperti training data.
        """
        data_rows = []
        
        # Hitung BMI
        user_bmi = user.weight / ((user.height / 100) ** 2)
        
        # Hitung hari dari target date
        from datetime import date
        target_date_days = (goal.target_date - date.today()).days
        
        for food in foods:
            row = {
                # Fitur pengguna
                'user_age': user.age,
                'user_weight': user.weight,
                'user_height': user.height,
                'user_bmi': user_bmi,
                
                # Fitur tujuan diet
                'target_weight': goal.target_weight,
                'target_date_days_from_now': target_date_days,
                
                # Fitur makanan
                'food_caloric_value': food.caloric_value or 0,
                'food_protein': food.protein or 0,
                'food_carbohydrates': food.carbohydrates or 0,
                'food_fat': food.fat or 0,
                'food_dietary_fiber': food.dietary_fiber or 0,
                'food_sodium': food.sodium or 0,
                'food_potassium': food.potassium or 0,
                'food_calcium': food.calcium or 0,
                'food_iron': food.iron or 0,
                'food_zinc': food.zinc or 0,
                'food_vitamin_c': food.vitamin_c or 0,
            }
            
            # One-hot encoding untuk kondisi medis
            medical_conditions = ['diabetes', 'hypertension', 'none', 'obesity']
            for condition in medical_conditions:
                row[f'medical_condition_{condition}'] = 1 if goal.medical_condition == condition else 0
            
            # One-hot encoding untuk preferensi diet
            diet_preferences = ['halal', 'vegetarian']
            for pref in diet_preferences:
                row[f'diet_preference_{pref}'] = 1 if pref in preferences else 0
            
            # One-hot encoding untuk alergi
            allergies = ['dairy_free', 'egg_free', 'nut_free', 'seafood_free', 'soy_free']
            for allergy in allergies:
                row[f'allergy_{allergy}'] = 1 if allergy in preferences else 0
            
            # One-hot encoding untuk gender
            genders = ['F', 'M']
            for gender in genders:
                row[f'gender_{gender}'] = 1 if user.gender == gender else 0
            
            # One-hot encoding untuk aktivitas
            activities = ['active', 'light', 'moderate', 'sedentary', 'very_active']
            for activity in activities:
                row[f'activity_{activity}'] = 1 if user.activity_level == activity else 0
            
            # One-hot encoding untuk status makanan
            food_statuses = ['Bahan Dasar', 'Olahan', 'Tunggal']
            for status in food_statuses:
                row[f'food_status_{status}'] = 1 if food.food_status == status else 0
            
            # One-hot encoding untuk grup makanan
            food_groups = [
                'Bahan makanan sumber energi', 'Bahan makanan sumber lemak',
                'Bahan makanan sumber protein hewani', 'Bahan makanan sumber protein nabati',
                'Bahan makanan sumber vitamin dan mineral', 'Makanan jadi',
                'Minuman', 'Rempah dan bumbu'
            ]
            for group in food_groups:
                row[f'food_group_{group}'] = 1 if food.food_group == group else 0
            
            # One-hot encoding untuk meal type
            meal_types = ['Bahan Dasar', 'Cemilan', 'Makan Malam', 'Makan Siang', 'Sarapan']
            for meal_type in meal_types:
                row[f'meal_type_{meal_type}'] = 1 if food.meal_type == meal_type else 0
            
            data_rows.append(row)
        
        df = pd.DataFrame(data_rows)
        
        # Pastikan semua kolom yang diperlukan ada
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Urutkan kolom sesuai dengan yang digunakan saat training
        df = df[self.feature_columns]
        
        # Handle missing values
        df = df.fillna(0)
        
        return df
    
    def _calculate_medical_bonus(self, food: Food, medical_condition: str) -> float:
        """
        Hitung bonus untuk kondisi medis tertentu.
        """
        if medical_condition == 'none':
            return 0.0
        
        bonus = 0.0
        food_name_lower = food.name.lower()
        
        if medical_condition == 'diabetes':
            # Bonus untuk makanan rendah karbohidrat dan tinggi serat
            if food.carbohydrates and food.carbohydrates < 15:
                bonus += 0.3
            if food.dietary_fiber and food.dietary_fiber > 5:
                bonus += 0.2
            # Penalti untuk makanan manis
            if any(keyword in food_name_lower for keyword in ['manis', 'gula', 'sirup']):
                bonus -= 0.3
                
        elif medical_condition == 'hypertension':
            # Bonus untuk makanan rendah sodium dan tinggi potassium
            if food.sodium and food.sodium < 200:
                bonus += 0.3
            if food.potassium and food.potassium > 300:
                bonus += 0.2
            # Penalti untuk makanan asin/olahan
            if any(keyword in food_name_lower for keyword in ['asin', 'dendeng', 'keripik']):
                bonus -= 0.3
                
        elif medical_condition == 'obesity':
            # Bonus untuk makanan rendah kalori dan tinggi protein
            if food.caloric_value and food.caloric_value < 200:
                bonus += 0.3
            if food.protein and food.protein > 15:
                bonus += 0.2
            # Penalti untuk makanan tinggi lemak/goreng
            if any(keyword in food_name_lower for keyword in ['goreng', 'keripik']):
                bonus -= 0.3
        
        return max(-0.5, min(0.5, bonus))
    
    def _get_fallback_recommendations(
        self,
        user: User,
        goal: DietGoal,
        preferences: List[str],
        food_ids_to_consider: Optional[List[int]],
        n_recommendations: int
    ) -> List[Dict]:
        """
        Fallback rekomendasi jika model ML tidak tersedia.
        Menggunakan scoring sederhana berdasarkan kondisi medis.
        """
        foods = self._get_foods_to_evaluate(food_ids_to_consider)
        recommendations = []
        
        for food in foods:
            # Scoring sederhana berdasarkan kalori dan kondisi medis
            score = 0.5  # Base score
            
            # Adjustments berdasarkan kondisi medis
            if goal.medical_condition == 'diabetes':
                if food.carbohydrates and food.carbohydrates < 20:
                    score += 0.2
                if food.carbohydrates and food.carbohydrates > 30:
                    score -= 0.3
                    
            elif goal.medical_condition == 'obesity':
                if food.caloric_value and food.caloric_value < 250:
                    score += 0.2
                if food.caloric_value and food.caloric_value > 400:
                    score -= 0.3
                    
            elif goal.medical_condition == 'hypertension':
                if food.sodium and food.sodium < 200:
                    score += 0.2
                if food.sodium and food.sodium > 400:
                    score -= 0.3
            
            score = max(0, min(1, score))
            
            recommendations.append({
                'food_id': food.id,
                'ml_score': score,
                'raw_ml_prediction': score,
                'medical_bonus': 0.0
            })
        
        recommendations.sort(key=lambda x: x['ml_score'], reverse=True)
        return recommendations[:n_recommendations]
    
    def get_model_info(self) -> Dict:
        """
        Dapatkan informasi tentang model yang dimuat.
        """
        if not self.is_loaded:
            return {'loaded': False}
        
        try:
            return {
                'loaded': True,
                'model_type': type(self.model).__name__,
                'model_path': self.model_path,
                'feature_count': len(self.feature_columns),
                'weights': {
                    'ml_prediction': self.ml_prediction_weight,
                    'medical_condition': self.medical_condition_weight,
                    'diversity': self.diversity_weight
                }
            }
        except Exception as e:
            return {'loaded': True, 'error': str(e)}