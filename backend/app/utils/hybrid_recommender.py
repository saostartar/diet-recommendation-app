from typing import List, Dict
from app.utils.collaborative_filtering import DietCollaborativeFiltering
from app.utils.decision_tree import NutritionDecisionTree
from app.utils.food_ml_classifier import FoodMLClassifier
from app.models.user import User
from app.models.recommendation import DietGoal, Recommendation
from app.models.food import Food
from app import db

class HybridDietRecommender:
    def __init__(self):
        self.cf_recommender = DietCollaborativeFiltering(n_neighbors=5)
        self.nutrition_recommender = NutritionDecisionTree()
        self.ml_classifier = FoodMLClassifier()
        self.cf_weight = 0.3
        self.nutrition_weight = 0.7

    def update_weights(self, user_id: int, food_id: int, rating: int) -> None:
        """
        Update recommendation weights based on user feedback
        """
        try:
            # Get user's previous ratings for this food
            previous_ratings = Recommendation.query.filter_by(
                user_id=user_id,
                food_id=food_id,
                rating=rating
            ).count()

            # Adjust weights based on rating
            if rating >= 4:  # Good rating
                if previous_ratings > 3:  # User consistently likes this type of food
                    self.cf_weight = min(0.4, self.cf_weight + 0.05)  # Increase CF weight
                    self.nutrition_weight = 1 - self.cf_weight
            elif rating <= 2:  # Poor rating
                if previous_ratings > 3:  # User consistently dislikes this type of food
                    self.cf_weight = max(0.2, self.cf_weight - 0.05)  # Decrease CF weight
                    self.nutrition_weight = 1 - self.cf_weight

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"Error updating weights: {str(e)}")
            raise

    def get_recommendations(
        self,
        user: User,
        goal: DietGoal,
        n_recommendations: int = 500,  # Increased to get more options per meal type
        preferences: List[str] = None
    ) -> List[Dict]:
        """
        Combines recommendations from CF and Decision Tree,
        then applies preference filtering and meal type classification
        """
        # Step 1: Get nutrition recommendations (they're already Indonesian only)
        nutrition_recs = self.nutrition_recommender.get_nutrition_recommendations(
            user,
            goal,
            n_recommendations=n_recommendations * 2
        )
        
        # Step 2: Get collaborative filtering recommendations
        cf_recs = self.cf_recommender.get_recommendations(
            user.id,
            n_recommendations=n_recommendations * 2
        )
        
        # Step 3: Combine recommendations with weights
        food_scores = {}
        
        # Process CF recommendations
        for rec in cf_recs:
            food = Food.query.get(rec['food_id'])
            if not food:
                continue
                
            food_scores[rec['food_id']] = {
                'food': food,
                'score': rec['cf_score'] * self.cf_weight,
                'cf_score': rec['cf_score'],
                'nutrition_score': 0
            }
            
        # Process nutrition recommendations
        for rec in nutrition_recs:
            food = Food.query.get(rec['food_id'])
            if not food:
                continue
                
            if rec['food_id'] in food_scores:
                food_scores[rec['food_id']]['nutrition_score'] = rec['nutrition_score']
                food_scores[rec['food_id']]['score'] += rec['nutrition_score'] * self.nutrition_weight
            else:
                food_scores[rec['food_id']] = {
                    'food': food,
                    'score': rec['nutrition_score'] * self.nutrition_weight,
                    'cf_score': 0,
                    'nutrition_score': rec['nutrition_score']
                }

        # Step 4: Filter based on preferences
        filtered_scores = {}
        if preferences:
            for food_id, data in food_scores.items():
                if self._matches_preferences(data['food'], preferences):
                    filtered_scores[food_id] = data
        else:
            filtered_scores = food_scores

        # Step 5: Classify each food by meal type
        classification_success = 0
        fallback_count = 0

        for food_id, data in filtered_scores.items():
            food = data['food']
            
            try:
                # Predict food status (Mentah/Olahan)
                food_status = self.ml_classifier.predict_food_status(
                    food.name, 
                    food.caloric_value, 
                    food.protein,
                    food.fat,
                    food.carbohydrates
                )
                
                # Predict meal type
                meal_type = self.ml_classifier.predict_meal_type(
                    food.name,
                    food.caloric_value,
                    food.protein,
                    food.fat,
                    food.carbohydrates,
                    food_status
                )
                
                classification_success += 1
                
            except Exception as e:
                # Fallback classification if prediction fails
                fallback_count += 1
                if food.caloric_value < 200:
                    food_status = 'Mentah'
                    meal_type = 'Cemilan'
                elif food.caloric_value > 500:
                    food_status = 'Olahan'
                    meal_type = 'Makan Malam'
                else:
                    food_status = 'Olahan' 
                    meal_type = 'Makan Siang'
                    
            # Store predictions with the food data
            data['food_status'] = food_status
            data['meal_type'] = meal_type
            data['is_model_prediction'] = True

        if fallback_count > 0:
            print(f"Used fallback classification for {fallback_count} foods")

        # Step 6: Sort and return top recommendations with meal type info
        final_recommendations = []
        for food_id, data in filtered_scores.items():
            final_recommendations.append({
                'food_id': food_id,
                'total_score': data['score'],
                'cf_score': data['cf_score'],
                'nutrition_score': data['nutrition_score'],
                'food_status': data['food_status'],
                'meal_type': data['meal_type']
            })
        
        # Sort by score and return all recommendations
        return sorted(final_recommendations, key=lambda x: x['total_score'], reverse=True)
    
    
    
    def _matches_preferences(self, food: Food, preferences: List[str]) -> bool:
        """Check if food matches user dietary preferences and allergy restrictions"""
        if not preferences:
            return True
            
        # Check each preference against food attributes
        for pref in preferences:
            # Check diet type
            if pref == 'vegetarian' and not food.is_vegetarian:
                print(f"Food {food.name} rejected: not vegetarian")
                return False
            elif pref == 'halal' and not food.is_halal:
                print(f"Food {food.name} rejected: not halal")
                return False
                
            # Check allergies using more careful detection from food name
            name_lower = food.name.lower()
            
            # Dairy allergy check
            if pref == 'dairy_free' and (
                food.contains_dairy or 
                any(kw in name_lower for kw in ['susu', 'keju', 'yogurt', 'krim', 'mentega'])
            ):
                print(f"Food {food.name} rejected: contains dairy")
                return False
                
            # Nut allergy check  
            if pref == 'nut_free' and (
                food.contains_nuts or
                any(kw in name_lower for kw in ['kacang', 'mete', 'almond', 'kenari'])
            ):
                print(f"Food {food.name} rejected: contains nuts")
                return False
                
            # Seafood allergy check
            if pref == 'seafood_free' and (
                food.contains_seafood or
                any(kw in name_lower for kw in ['ikan', 'udang', 'cumi', 'kerang', 'laut', 'seafood'])
            ):
                print(f"Food {food.name} rejected: contains seafood")
                return False
                
            # Egg allergy check
            if pref == 'egg_free' and (
                food.contains_eggs or
                'telur' in name_lower
            ):
                print(f"Food {food.name} rejected: contains eggs")
                return False
                
            # Soy allergy check
            if pref == 'soy_free' and (
                food.contains_soy or
                any(kw in name_lower for kw in ['kedelai', 'tahu', 'tempe', 'kecap'])
            ):
                print(f"Food {food.name} rejected: contains soy")
                return False
                
        return True