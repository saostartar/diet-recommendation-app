from typing import List, Dict
from app.utils.collaborative_filtering import DietCollaborativeFiltering
from app.utils.decision_tree import NutritionDecisionTree
from app.utils.food_ml_classifier import FoodMLClassifier
from app.models.user import User
from app.models.recommendation import DietGoal, Recommendation, FoodPreference
from app.models.food import Food
from app import db
import random

class HybridDietRecommender:
    def __init__(self):
        self.cf_recommender = DietCollaborativeFiltering(n_neighbors=5)
        self.nutrition_recommender = NutritionDecisionTree()
        self.ml_classifier = FoodMLClassifier()
        self.cf_weight = 0.3
        self.nutrition_weight = 0.7
        self.diversity_factor = 0.2  # Factor for promoting diversity

    def update_weights(self, user_id: int, food_id: int, rating: int) -> None:
        """Update recommendation weights based on user feedback."""
        try:
            previous_ratings_count = Recommendation.query.filter_by(
                user_id=user_id,
                food_id=food_id
            ).filter(Recommendation.rating.isnot(None)).count()

            if rating >= 4:  # User likes the food
                if previous_ratings_count > 2:
                    self.cf_weight = min(0.5, self.cf_weight + 0.02)
                    self.nutrition_weight = max(0.5, 1 - self.cf_weight)
            elif rating <= 2:  # User dislikes the food
                self.nutrition_weight = min(0.8, self.nutrition_weight + 0.05)
                self.cf_weight = max(0.2, 1 - self.nutrition_weight)
        except Exception as e:
            print(f"Error updating weights: {e}")

    def get_recommendations(
        self,
        user: User,
        goal: DietGoal,
        preferences: List[str] = None,
        total_initial_candidates: int = 500,
        items_per_meal_type: Dict[str, int] = None
    ) -> List[Dict]:
        """Get diverse food recommendations for all meal types."""
        
        if items_per_meal_type is None:
            items_per_meal_type = {
                'Sarapan': 5,
                'Makan Siang': 5,
                'Makan Malam': 5,
                'Cemilan': 5
            }

        # 1. Get all foods and apply preference filtering first
        all_foods = Food.query.all()
        if not all_foods:
            return []

        # Filter foods by preferences early
        filtered_foods = []
        for food in all_foods:
            if self._matches_preferences(food, preferences or []):
                filtered_foods.append(food)

        if not filtered_foods:
            print("No foods match user preferences")
            return []

        print(f"Foods after preference filtering: {len(filtered_foods)}")

        # 2. Get nutrition recommendations for filtered foods
        nutrition_recs = self.nutrition_recommender.get_nutrition_recommendations(
            user, goal, n_recommendations=len(filtered_foods)
        )

        # 3. Get collaborative filtering recommendations
        cf_recs = self.cf_recommender.get_recommendations(
            user.id, n_recommendations=min(total_initial_candidates, len(filtered_foods))
        )

        # 4. Create comprehensive food scoring
        food_scores = {}
        
        # Initialize with nutrition scores
        for rec in nutrition_recs:
            food = Food.query.get(rec['food_id'])
            if food and food in filtered_foods:
                food_scores[rec['food_id']] = {
                    'food': food,
                    'nutrition_score': rec['nutrition_score'],
                    'cf_score': 0.0,
                    'diversity_bonus': 0.0,
                    'medical_bonus': 0.0
                }

        # Add CF scores
        for rec in cf_recs:
            if rec['food_id'] in food_scores:
                food_scores[rec['food_id']]['cf_score'] = rec['cf_score']

        # 5. Add medical condition bonuses
        self._add_medical_condition_bonuses(food_scores, goal.medical_condition)

        # 6. Classify meal types and group by meal type
        meal_type_groups = {
            'Sarapan': [],
            'Makan Siang': [],
            'Makan Malam': [],
            'Cemilan': []
        }

        for food_id, data in food_scores.items():
            food_obj = data['food']
            
            try:
                meal_type = self.ml_classifier.predict_meal_type(
                    food_obj.name,
                    food_obj.energy_kj,
                    food_obj.protein,
                    food_obj.fat,
                    food_obj.carbohydrates
                )
            except Exception as e:
                print(f"Error classifying meal type for {food_obj.name}: {e}")
                meal_type = self._classify_meal_type_by_calories(food_obj)

            if meal_type in meal_type_groups:
                # Calculate final score
                final_score = (
                    data['nutrition_score'] * self.nutrition_weight +
                    data['cf_score'] * self.cf_weight +
                    data['medical_bonus'] * 0.1
                )
                
                meal_type_groups[meal_type].append({
                    'food_id': food_id,
                    'food_object': food_obj,
                    'total_score': final_score,
                    'cf_score': data['cf_score'],
                    'nutrition_score': data['nutrition_score'],
                    'meal_type': meal_type,
                    'medical_bonus': data['medical_bonus']
                })

        # 7. Select diverse recommendations for each meal type
        final_recommendations = []
        
        for meal_type, candidates in meal_type_groups.items():
            if not candidates:
                continue
                
            # Sort by score
            candidates.sort(key=lambda x: x['total_score'], reverse=True)
            
            # Select diverse items
            selected = self._select_diverse_items(
                candidates, 
                items_per_meal_type.get(meal_type, 5),
                user
            )
            
            final_recommendations.extend(selected)

        return final_recommendations

    def _add_medical_condition_bonuses(self, food_scores: Dict, medical_condition: str):
        """Add bonuses based on medical conditions."""
        for food_id, data in food_scores.items():
            food = data['food']
            bonus = 0.0
            
            if medical_condition == 'diabetes':
                # Prefer low carb, high fiber foods
                if food.carbohydrates and food.carbohydrates < 15:
                    bonus += 0.3
                if food.dietary_fiber and food.dietary_fiber > 3:
                    bonus += 0.2
                if food.caloric_value and food.caloric_value < 200:
                    bonus += 0.1
                    
            elif medical_condition == 'hypertension':
                # Prefer low sodium, high potassium foods
                if food.sodium and food.sodium < 300:
                    bonus += 0.3
                if food.potassium and food.potassium > 200:
                    bonus += 0.2
                if food.fat and food.fat < 5:
                    bonus += 0.1
                    
            elif medical_condition == 'obesity':
                # Prefer low calorie, high protein foods
                if food.caloric_value and food.caloric_value < 150:
                    bonus += 0.3
                if food.protein and food.protein > 10:
                    bonus += 0.2
                if food.fat and food.fat < 3:
                    bonus += 0.1
                    
            data['medical_bonus'] = bonus

    def _select_diverse_items(self, candidates: List[Dict], target_count: int, user: User) -> List[Dict]:
        """Select diverse items from candidates."""
        if len(candidates) <= target_count:
            return candidates
            
        selected = []
        remaining = candidates.copy()
        
        # Always include top scorer
        if remaining:
            selected.append(remaining.pop(0))
        
        # Get user's recent foods to avoid repetition
        recent_foods = self._get_recent_user_foods(user.id, days=7)
        
        while len(selected) < target_count and remaining:
            best_candidate = None
            best_diversity_score = -1
            
            for i, candidate in enumerate(remaining):
                # Skip if user had this food recently
                if candidate['food_id'] in recent_foods:
                    continue
                    
                diversity_score = self._calculate_diversity_score(
                    candidate, selected
                )
                
                # Combine with recommendation score
                combined_score = (
                    candidate['total_score'] * 0.7 + 
                    diversity_score * 0.3
                )
                
                if combined_score > best_diversity_score:
                    best_diversity_score = combined_score
                    best_candidate = (i, candidate)
            
            if best_candidate:
                selected.append(remaining.pop(best_candidate[0]))
            else:
                # If no diverse candidate found, pick next best
                if remaining:
                    selected.append(remaining.pop(0))
        
        return selected

    def _calculate_diversity_score(self, candidate: Dict, selected: List[Dict]) -> float:
        """Calculate diversity score for a candidate."""
        if not selected:
            return 1.0
            
        candidate_food = candidate['food_object']
        diversity_score = 1.0
        
        for selected_item in selected:
            selected_food = selected_item['food_object']
            
            # Check ingredient similarity (simplified)
            if self._foods_are_similar(candidate_food, selected_food):
                diversity_score *= 0.5
                
        return diversity_score

    def _foods_are_similar(self, food1: Food, food2: Food) -> bool:
        """Check if two foods are similar."""
        name1 = food1.name.lower()
        name2 = food2.name.lower()
        
        # Check for common ingredients
        common_ingredients = [
            'ayam', 'sapi', 'ikan', 'udang', 'telur',
            'nasi', 'mie', 'roti', 'kentang',
            'tahu', 'tempe', 'sayur'
        ]
        
        for ingredient in common_ingredients:
            if ingredient in name1 and ingredient in name2:
                return True
                
        return False

    def _get_recent_user_foods(self, user_id: int, days: int = 7) -> set:
        """Get foods user consumed recently."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        recent_recs = Recommendation.query.filter(
            Recommendation.user_id == user_id,
            Recommendation.recommendation_date >= cutoff_date,
            Recommendation.is_consumed == True
        ).all()
        
        return {rec.food_id for rec in recent_recs}

    def _classify_meal_type_by_calories(self, food: Food) -> str:
        """Fallback meal type classification by calories."""
        if not food.caloric_value:
            return 'Cemilan'
            
        if food.caloric_value < 100:
            return 'Cemilan'
        elif food.caloric_value < 250:
            return 'Sarapan'
        elif food.caloric_value < 400:
            return 'Makan Siang'
        else:
            return 'Makan Malam'

    def _matches_preferences(self, food: Food, preferences: List[str]) -> bool:
        """Check if food matches user preferences."""
        if not preferences:
            return True
            
        for pref_type in preferences:
            if pref_type == 'vegetarian' and not food.is_vegetarian:
                return False
            if pref_type == 'halal' and not food.is_halal:
                return False
            if pref_type == 'dairy_free' and food.contains_dairy:
                return False
            if pref_type == 'nut_free' and food.contains_nuts:
                return False
            if pref_type == 'seafood_free' and food.contains_seafood:
                return False
            if pref_type == 'egg_free' and food.contains_eggs:
                return False
            if pref_type == 'soy_free' and food.contains_soy:
                return False
                
        return True