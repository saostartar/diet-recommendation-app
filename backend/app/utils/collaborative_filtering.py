import numpy as np
from sklearn.neighbors import NearestNeighbors
from app.models.user import User
from app.models.recommendation import Recommendation, DietGoal
from app.models.food import Food
from sqlalchemy import func
from typing import Dict, List, Tuple
from app import db

class DietCollaborativeFiltering:
    def __init__(self, n_neighbors: int = 5):
        self.k = n_neighbors
        self.model = NearestNeighbors(
            n_neighbors=n_neighbors,
            metric='cosine',
            algorithm='brute'
        )

    def _create_user_profile_matrix(self) -> Tuple[np.ndarray, List[int]]:
        """
        Membuat matriks profil user berdasarkan:
        1. Karakteristik kesehatan (BMI, usia)
        2. Activity level
        3. Medical condition
        4. Preferensi makanan (rating)
        """
        users = User.query.all()
        user_ids = [user.id for user in users]
        
        # Matriks profil (n_users x n_features)
        profile_matrix = np.zeros((len(users), 7))
        
        for idx, user in enumerate(users):
            # Normalisasi BMI
            height_m = user.height / 100
            bmi = user.weight / (height_m ** 2)
            profile_matrix[idx, 0] = self._normalize_value(bmi, 18.5, 30)
            
            # Normalisasi usia
            profile_matrix[idx, 1] = self._normalize_value(user.age, 18, 80)
            
            # Activity level encoding
            activity_levels = {
                'sedentary': 0, 'light': 0.25,
                'moderate': 0.5, 'active': 0.75,
                'very_active': 1
            }
            profile_matrix[idx, 2] = activity_levels[user.activity_level]
            
            # Medical condition encoding (replacing the previous goal_type encoding)
            goal = DietGoal.query.filter_by(
                user_id=user.id,
                status='active'
            ).first()
            
            # Default encoding for medical conditions
            med_condition_encoding = [0, 0, 0]
            
            if goal:
                conditions = {
                    'diabetes': [1, 0, 0],
                    'hypertension': [0, 1, 0],
                    'obesity': [0, 0, 1],
                    'none': [0, 0, 0]
                }
                med_condition_encoding = conditions.get(goal.medical_condition, [0, 0, 0])
            
            profile_matrix[idx, 3:6] = med_condition_encoding
            
            # Rating preference
            avg_rating = db.session.query(func.avg(Recommendation.rating))\
                .filter_by(user_id=user.id)\
                .scalar() or 0
            profile_matrix[idx, 6] = avg_rating / 5  # Normalize to 0-1
            
        return profile_matrix, user_ids

    def _normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """Normalisasi nilai ke range 0-1"""
        return min(1.0, max(0.0, (value - min_val) / (max_val - min_val)))

    def get_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Dict]:
        """Mendapatkan rekomendasi makanan untuk user"""
        profile_matrix, user_ids = self._create_user_profile_matrix()
        
        # If not enough users for collaborative filtering
        if len(user_ids) < self.k:
            return self._get_fallback_recommendations(n_recommendations)
        
        # Fit model
        self.model.fit(profile_matrix)
        
        # Dapatkan user index
        try:
            user_idx = user_ids.index(user_id)
        except ValueError:
            # If user not found, fall back to default recommendations
            return self._get_fallback_recommendations(n_recommendations)
            
        user_profile = profile_matrix[user_idx].reshape(1, -1)
        
        # Cari k tetangga terdekat
        distances, indices = self.model.kneighbors(user_profile)
        
        # Dapatkan rekomendasi dari tetangga
        similar_users = [user_ids[idx] for idx in indices[0]]
        
        # Ambil makanan yang disukai oleh similar users
        recommended_foods = {}
        for sim_user_id in similar_users:
            # Ambil makanan dengan rating tinggi
            good_recommendations = Recommendation.query\
                .filter_by(user_id=sim_user_id)\
                .filter(Recommendation.rating >= 4)\
                .all()
                
            for rec in good_recommendations:
                if rec.food_id not in recommended_foods:
                    recommended_foods[rec.food_id] = {
                        'score': 0,
                        'count': 0
                    }
                recommended_foods[rec.food_id]['score'] += rec.rating
                recommended_foods[rec.food_id]['count'] += 1
        
        # Hitung skor akhir
        final_recommendations = []
        for food_id, data in recommended_foods.items():
            avg_score = data['score'] / data['count']
            final_recommendations.append({
                'food_id': food_id,
                'cf_score': avg_score / 5  # Normalize to 0-1
            })
        
        # Sort dan ambil n rekomendasi teratas
        return sorted(
            final_recommendations,
            key=lambda x: x['cf_score'],
            reverse=True
        )[:n_recommendations]
     
    def _get_fallback_recommendations(self, n_recommendations: int) -> List[Dict]:
        """Fallback to simple recommendations when not enough users"""
        # Get highest rated foods
        top_foods = Food.query\
            .join(Recommendation)\
            .group_by(Food.id)\
            .order_by(func.avg(Recommendation.rating).desc())\
            .limit(n_recommendations)\
            .all()
            
        # If no rated foods yet, get any foods
        if not top_foods:
            top_foods = Food.query.limit(n_recommendations).all()
            
        return [
            {
                'food_id': food.id,
                'cf_score': 0.5  # neutral score
            }
            for food in top_foods
        ]