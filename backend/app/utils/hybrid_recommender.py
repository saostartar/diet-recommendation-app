from typing import List, Dict, Optional
from app.utils.collaborative_filtering import DietCollaborativeFiltering
from app.utils.decision_tree import NutritionDecisionTree
from app.models.user import User
from app.models.recommendation import DietGoal, Recommendation, FoodPreference
from app.models.food import Food
from app import db
import random
from datetime import datetime, timedelta 
from collections import Counter

class HybridDietRecommender:
    def __init__(self):
        self.cf_recommender = DietCollaborativeFiltering(n_neighbors=5)
        self.nutrition_recommender = NutritionDecisionTree()
        # Adjusted weights: more emphasis on preparation, slightly less on nutrition for general balance
        self.cf_weight = 0.25 
        self.nutrition_weight = 0.45
        self.preparation_priority_weight = 0.25 
        # This represents the conceptual weight for medical_bonus in the final score sum
        self.medical_bonus_weight_component = 0.05 


    def update_weights(self, user_id: int, food_id: int, rating: int) -> None:
        """Update recommendation weights based on user feedback."""
        try:
            previous_ratings_count = Recommendation.query.filter_by(
                user_id=user_id,
                food_id=food_id
            ).filter(Recommendation.rating.isnot(None)).count()

            # Simple dynamic adjustment based on rating
            if rating >= 4: # User likes it, CF might be more important
                self.cf_weight = min(0.35, self.cf_weight + 0.01)
                self.nutrition_weight = max(0.35, self.nutrition_weight - 0.005)
                self.preparation_priority_weight = max(0.20, self.preparation_priority_weight - 0.005)
            elif rating <= 2: # User dislikes it, CF might be less reliable or nutrition/prep was off
                self.cf_weight = max(0.15, self.cf_weight - 0.01)
                self.nutrition_weight = min(0.55, self.nutrition_weight + 0.005)
                self.preparation_priority_weight = min(0.30, self.preparation_priority_weight + 0.005)
            
            # Ensure weights sum up correctly with medical_bonus_weight_component
            # Let current sum of 3 be X. We want X + medical_bonus_weight_component = 1. So X = 1 - medical_bonus_weight_component
            target_sum_for_three = 1.0 - self.medical_bonus_weight_component
            current_sum_for_three = self.cf_weight + self.nutrition_weight + self.preparation_priority_weight
            
            if current_sum_for_three > 0: # Avoid division by zero
                self.cf_weight = (self.cf_weight / current_sum_for_three) * target_sum_for_three
                self.nutrition_weight = (self.nutrition_weight / current_sum_for_three) * target_sum_for_three
                self.preparation_priority_weight = (self.preparation_priority_weight / current_sum_for_three) * target_sum_for_three
            else: # Fallback if sum is zero (should not happen with positive weights)
                self.cf_weight = 0.25 * target_sum_for_three / 0.95
                self.nutrition_weight = 0.45 * target_sum_for_three / 0.95
                self.preparation_priority_weight = 0.25 * target_sum_for_three / 0.95


        except Exception as e:
            print(f"Error updating weights: {e}")

    def _matches_preferences(self, food: Food, preferences: List[str]) -> bool:
        """Check if food matches user preferences (halal, vegetarian, allergies)."""
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

    def get_recommendations(
        self,
        user: User,
        goal: DietGoal,
        preferences: List[str] = None,
        total_initial_candidates: int = 700,
        items_per_meal_type: Optional[Dict[str, int]] = None 
    ) -> List[Dict]:
        """Get diverse food recommendations for all meal types."""
        
        if items_per_meal_type is None: 
            items_per_meal_type = {
                'Sarapan': 10, 'Makan Siang': 10, 'Makan Malam': 10, 'Cemilan': 10
            }

        all_foods_query = Food.query.filter(Food.caloric_value.isnot(None))
        # Exclude "Bahan Dasar" from being directly recommended as full meals initially
        # They can still be part of CF if rated, or nutrition if their components are analyzed.
        # For this system, if they are directly scorable for nutrition, they might pass through.
        # Let's keep them for now and see if scoring/classification handles them.
        all_foods = all_foods_query.all()


        if not all_foods:
            return []

        filtered_foods = [
            food for food in all_foods if self._matches_preferences(food, preferences or [])
        ]

        if not filtered_foods:
            print(f"User {user.id}: No foods match preferences: {preferences}")
            return []
        
        nutrition_recs_input_ids = [f.id for f in filtered_foods]
        nutrition_recs = self.nutrition_recommender.get_nutrition_recommendations(
            user, goal, n_recommendations=len(filtered_foods), food_ids_to_consider=nutrition_recs_input_ids
        )

        cf_recs = self.cf_recommender.get_recommendations(
            user.id, n_recommendations=min(total_initial_candidates, len(filtered_foods))
        )

        food_scores = {}
        for rec in nutrition_recs:
            food_obj_from_filtered = next((f for f in filtered_foods if f.id == rec['food_id']), None)
            if food_obj_from_filtered:
                food_scores[rec['food_id']] = {
                    'food': food_obj_from_filtered,
                    'nutrition_score': rec['nutrition_score'],
                    'cf_score': 0.0,
                    'medical_bonus': 0.0 
                }
        
        for rec in cf_recs:
            if rec['food_id'] in food_scores:
                food_scores[rec['food_id']]['cf_score'] = rec['cf_score']
            elif rec['food_id'] not in food_scores: # Food from CF not in nutrition_recs (e.g. not matching preferences after nutrition filtering)
                food_obj_from_all = next((f for f in all_foods if f.id == rec['food_id']), None)
                if food_obj_from_all and self._matches_preferences(food_obj_from_all, preferences or []):
                     food_scores[rec['food_id']] = {
                        'food': food_obj_from_all,
                        'nutrition_score': 0.3, # Assign a neutral default nutrition score
                        'cf_score': rec['cf_score'],
                        'medical_bonus': 0.0
                    }


        self._add_medical_condition_bonuses(food_scores, goal.medical_condition)

        meal_type_groups = { 'Sarapan': [], 'Makan Siang': [], 'Makan Malam': [], 'Cemilan': [] }

        for food_id, data in food_scores.items():
            food_obj = data['food']
            
            # Use meal_type from CSV if valid, otherwise classify
            assigned_meal_type = food_obj.meal_type
            if not assigned_meal_type or assigned_meal_type not in meal_type_groups or assigned_meal_type == "Bahan Dasar":
                assigned_meal_type = self._classify_meal_type_by_calories(food_obj)
            
            # Ensure it falls into one of the defined groups
            if assigned_meal_type not in meal_type_groups:
                assigned_meal_type = 'Cemilan' # Default fallback

            preparation_priority_score_value = 0.5 # Default score

            if food_obj.food_status == 'Bahan Dasar':
                preparation_priority_score_value = 0.05 # Very low, requires significant processing
            elif food_obj.food_status == 'Olahan':
                if 'mentah' in food_obj.name.lower(): 
                    preparation_priority_score_value = 0.3 
                else:
                    preparation_priority_score_value = 1.0 
            elif food_obj.food_status == 'Tunggal':
                preparation_priority_score_value = 0.2 
            
            current_cf_weight = self.cf_weight
            current_nutrition_weight = self.nutrition_weight
            current_prep_weight = self.preparation_priority_weight
            current_medical_bonus_weight = self.medical_bonus_weight_component
            
            total_weight_sum = current_cf_weight + current_nutrition_weight + current_prep_weight + current_medical_bonus_weight
            if total_weight_sum <= 0: total_weight_sum = 1 

            normalized_cf_w = current_cf_weight / total_weight_sum
            normalized_nut_w = current_nutrition_weight / total_weight_sum
            normalized_prep_w = current_prep_weight / total_weight_sum
            normalized_med_w = current_medical_bonus_weight / total_weight_sum


            final_score = (
                data.get('nutrition_score', 0) * normalized_nut_w + # Use .get for safety
                data.get('cf_score', 0) * normalized_cf_w +
                data.get('medical_bonus', 0) * normalized_med_w + 
                preparation_priority_score_value * normalized_prep_w
            )
            final_score = max(0, min(1, final_score))
            
            meal_type_groups[assigned_meal_type].append({
                'food_id': food_id, 'food_object': food_obj, 'total_score': final_score,
                'cf_score': data.get('cf_score',0), 
                'nutrition_score': data.get('nutrition_score',0),
                'meal_type': assigned_meal_type, 
                'medical_bonus': data.get('medical_bonus',0),
                'preparation_score_component': preparation_priority_score_value * normalized_prep_w 
            })

        final_recommendations = []
        for meal_type_key, candidates_for_meal in meal_type_groups.items():
            if not candidates_for_meal: continue
            
            # Sort candidates primarily by total_score
            candidates_for_meal.sort(key=lambda x: x['total_score'], reverse=True)
            
            count_for_this_meal = items_per_meal_type.get(meal_type_key, 5) 
            selected = self._select_diverse_items(candidates_for_meal, count_for_this_meal, user)
            final_recommendations.extend(selected)
            
        return final_recommendations

    def _add_medical_condition_bonuses(self, food_scores: Dict, medical_condition: str):
        """Enhanced medical condition bonuses with stricter criteria"""
        for food_id, data in food_scores.items():
            food = data['food']
            bonus = 0.0
            penalty = 0.0
            
            food_name_lower = food.name.lower()
            food_carbohydrates = food.carbohydrates if food.carbohydrates is not None else 0
            food_dietary_fiber = food.dietary_fiber if food.dietary_fiber is not None else 0
            food_caloric_value = food.caloric_value if food.caloric_value is not None else 0
            food_sodium = food.sodium if food.sodium is not None else 0
            food_potassium = food.potassium if food.potassium is not None else 0
            food_fat = food.fat if food.fat is not None else 0
            food_protein = food.protein if food.protein is not None else 0
    
            if medical_condition == 'diabetes':
                # Strong bonus for diabetes-friendly foods
                if food_carbohydrates < 10:
                    bonus += 0.4
                elif food_carbohydrates < 20:
                    bonus += 0.2
                
                if food_dietary_fiber > 5:
                    bonus += 0.3
                elif food_dietary_fiber > 3:
                    bonus += 0.2
                
                # Low calorie bonus
                if food_caloric_value < 200 and food_caloric_value > 0:
                    bonus += 0.2
                
                # Penalty for high carb foods
                if food_carbohydrates > 30:
                    penalty += 0.5
                
                # Penalty for sweet foods
                if any(keyword in food_name_lower for keyword in ['manis', 'gula', 'sirup', 'dodol', 'kue']):
                    penalty += 0.3
                    
            elif medical_condition == 'hypertension':
                # Strong bonus for low sodium foods
                if food_sodium < 100:
                    bonus += 0.4
                elif food_sodium < 200:
                    bonus += 0.3
                elif food_sodium < 300:
                    bonus += 0.1
                
                # High potassium bonus
                if food_potassium > 400:
                    bonus += 0.3
                elif food_potassium > 200:
                    bonus += 0.2
                
                # Low fat bonus
                if food_fat < 3:
                    bonus += 0.2
                
                # Strong penalty for high sodium foods
                if food_sodium > 500:
                    penalty += 0.6
                elif food_sodium > 300:
                    penalty += 0.3
                
                # Penalty for processed foods
                if any(keyword in food_name_lower for keyword in ['dendeng', 'asin', 'kering', 'keripik', 'abon']):
                    penalty += 0.4
                    
            elif medical_condition == 'obesity':
                # Strong bonus for low calorie foods
                if food_caloric_value < 150 and food_caloric_value > 0:
                    bonus += 0.4
                elif food_caloric_value < 250:
                    bonus += 0.2
                
                # High protein bonus (satiety)
                if food_protein > 15:
                    bonus += 0.3
                elif food_protein > 10:
                    bonus += 0.2
                
                # Low fat bonus
                if food_fat < 3:
                    bonus += 0.2
                elif food_fat < 5:
                    bonus += 0.1
                
                # High fiber bonus (satiety)
                if food_dietary_fiber > 5:
                    bonus += 0.3
                elif food_dietary_fiber > 3:
                    bonus += 0.2
                
                # Strong penalty for high calorie foods
                if food_caloric_value > 400:
                    penalty += 0.6
                elif food_caloric_value > 300:
                    penalty += 0.3
                
                # Penalty for fried foods
                if any(keyword in food_name_lower for keyword in ['goreng', 'keripik', 'dendeng', 'rempeyek']):
                    penalty += 0.4
            
            # Apply final score adjustment
            final_adjustment = bonus - penalty
            data['medical_bonus'] = max(-0.5, min(0.5, final_adjustment))

    def _select_diverse_items(self, candidates: List[Dict], target_count: int, user: User) -> List[Dict]:
        if not candidates: return []
        if len(candidates) <= target_count: return candidates
        
        selected_items = []
        # used_food_ids = set() # Not strictly needed if we iterate through pre-sorted candidates once
        recent_consumed_food_ids = self._get_recent_user_foods(user.id, days=3)

        # Create a temporary list of candidates with an adjusted score for selection
        # This adjusted score considers recency and group diversity penalties for sorting
        temp_candidates_for_selection = []
        for cand in candidates:
            is_recent = cand['food_id'] in recent_consumed_food_ids
            # Base score is the total_score already calculated
            selection_score = cand['total_score']
            if is_recent:
                selection_score -= 0.1 # Penalize recently consumed items

            temp_candidates_for_selection.append({**cand, 'selection_score': selection_score})
        
        # Sort by this new selection_score
        temp_candidates_for_selection.sort(key=lambda x: x['selection_score'], reverse=True)

        food_group_counts = Counter()
        # Max items from one food group for a meal. e.g., for 6 items, max ~2-3 from same group.
        # If target_count is small, allow more concentration.
        max_per_food_group = max(1, round(target_count * 0.45)) if target_count > 3 else target_count 


        for candidate in temp_candidates_for_selection:
            if len(selected_items) >= target_count:
                break

            food_obj = candidate['food_object']
            current_food_group = food_obj.food_group or "Unknown"

            # If this food group is already at its max for this meal, try to skip it
            # unless we are desperate for items.
            if food_group_counts[current_food_group] >= max_per_food_group:
                # Check if we still have slots left and other groups might be available
                # This is a soft limit: if other groups are exhausted, we might exceed this.
                # A simple way is to see if we are in the last few picks needed.
                if len(selected_items) < target_count -1 : # If not the very last item needed
                    continue 


            selected_items.append(candidate)
            food_group_counts[current_food_group] += 1
        
        # If after diversity attempt, we still don't have enough, fill with top original candidates
        if len(selected_items) < target_count:
            current_selected_ids = {item['food_id'] for item in selected_items}
            for cand in candidates: # candidates are already sorted by original total_score
                if len(selected_items) >= target_count:
                    break
                if cand['food_id'] not in current_selected_ids:
                    selected_items.append(cand)
                    current_selected_ids.add(cand['food_id'])
                    
        return selected_items[:target_count]


    def _get_recent_user_foods(self, user_id: int, days: int = 7) -> set:
        cutoff_date = datetime.now().date() - timedelta(days=days)
        recent_recs = Recommendation.query.filter(
            Recommendation.user_id == user_id,
            Recommendation.recommendation_date >= cutoff_date,
            ((Recommendation.is_consumed == True) | (Recommendation.rating >= 4)) 
        ).all()
        return {rec.food_id for rec in recent_recs}

    def _classify_meal_type_by_calories(self, food: Food) -> str:
        """
        Classify meal type based on CSV meal_type, then keywords and calories.
        Prioritizes valid meal_type from CSV first.
        """
        # 1. Use meal_type from CSV if it's one of the main categories
        valid_csv_meal_types = ['Sarapan', 'Makan Siang', 'Makan Malam', 'Cemilan']
        if food.meal_type and food.meal_type in valid_csv_meal_types:
            return food.meal_type
        
        # 2. If CSV meal_type is "Bahan Dasar" or not useful, classify
        calories_kcal = food.caloric_value if food.caloric_value is not None else 0
        name_lower = food.name.lower()
        food_group = food.food_group.lower() if food.food_group else ""
        
        breakfast_keywords = ['bubur', 'oatmeal', 'sereal', 'lontong', 'nasi uduk', 'nasi kuning', 'roti', 'sandwich', 'omelet', 'telur dadar', 'saridele']
        snack_keywords = ['kue', 'biskuit', 'keripik', 'gorengan', 'puding', 'es krim', 'eskrim', 'rujak', 'coklat', 'permen', 'yogurt', 'buah potong', 'kacang', 'rempeyek', 'pastel', 'risoles', 'kwaci', 'dodol', 'getuk', 'emping', 'geplak', 'wajit', 'wingko', 'onde-onde']
        drink_keywords = ['kopi', 'teh', 'jus', 'susu', 'smoothie', 'sirup', 'es '] # Note trailing space for 'es '

        if any(kw in name_lower for kw in breakfast_keywords) or 'serealia' in food_group and 'roti' in name_lower:
            if 50 < calories_kcal < 600 : return 'Sarapan' # Wider range for breakfast items
        if any(kw in name_lower for kw in snack_keywords) or 'buah' in food_group and calories_kcal < 350:
             # Exclude items that are substantial despite snack keywords
            if not (("martabak" in name_lower and "telur" in name_lower and calories_kcal > 250) or \
                    ("bakwan" in name_lower and calories_kcal > 200 and protein_g > 5)):
                if 20 < calories_kcal < 600 : return 'Cemilan' # Wider range for snack items

        if any(kw in name_lower for kw in drink_keywords) and calories_kcal < 350:
            if 'susu kental manis' not in name_lower and 'krimer' not in name_lower:
                 return 'Cemilan' # Drinks are usually snacks/part of breakfast

        # General calorie-based classification as fallback
        protein_g = food.protein if food.protein is not None else 0
        carbs_g = food.carbohydrates if food.carbohydrates is not None else 0

        if calories_kcal <= 0: return 'Cemilan'
        
        # More detailed calorie brackets
        if calories_kcal <= 250: # Low cal, likely snack or very light breakfast component
            if protein_g > 8 and carbs_g > 10 and 'serealia' in food_group: return 'Sarapan'
            return 'Cemilan'
        elif calories_kcal <= 500: # Medium cal
            if 'daging' in food_group or 'ikan' in food_group or 'telur' in food_group and protein_g > 15:
                 # Check if it's a clear breakfast item by name, otherwise could be light lunch
                if any(kw in name_lower for kw in breakfast_keywords): return 'Sarapan'
                return 'Makan Siang' 
            if 'serealia' in food_group and protein_g > 10 and carbs_g > 20: return 'Sarapan' # Substantial breakfast
            if 'nasi' in name_lower or 'mie' in name_lower or 'pasta' in name_lower : return 'Makan Siang'
            return 'Sarapan' # Default for this range if not clearly lunch/snack
        elif calories_kcal <= 800: # Higher cal, likely main meal
            if 'sayur' in food_group and protein_g < 10 : return 'Makan Siang' # e.g. Gado-gado like items
            return 'Makan Malam' # Default for this range
        else: # Very high cal
            return 'Makan Malam'