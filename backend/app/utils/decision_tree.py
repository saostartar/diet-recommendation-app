from typing import Dict, List, Optional
from app.models.user import User
from app.models.recommendation import DietGoal
from app.models.food import Food

class NutritionDecisionTree:
    def __init__(self):
        self.calorie_match_weight = 0.25
        self.protein_match_weight = 0.25
        self.carb_match_weight = 0.20
        self.fat_match_weight = 0.15
        self.micronutrient_adjustment_weight = 0.15

    def _is_suitable_for_medical_condition(self, food: Food, medical_condition: str) -> bool:
        """Check if food is suitable for specific medical condition"""
        if medical_condition == 'none':
            return True
            
        food_name_lower = food.name.lower()
        calories = food.caloric_value or 0
        carbs = food.carbohydrates or 0
        sodium = food.sodium or 0
        fat = food.fat or 0
        
        # High sodium foods to avoid for hypertension
        high_sodium_foods = [
            'dendeng', 'ikan asin', 'ikan kering', 'terasi', 'kerupuk', 
            'kecap', 'tauco', 'abon', 'sosis', 'kornet', 'sardines',
            'keripik', 'rempeyek', 'emping', 'krupuk'
        ]
        
        # High carb foods to limit for diabetes
        high_carb_foods = [
            'tepung', 'nasi', 'mie', 'pasta', 'roti manis', 'kue',
            'dodol', 'gula', 'sirup', 'es krim', 'permen'
        ]
        
        # High calorie fried foods to avoid for obesity
        high_cal_fried_foods = [
            'goreng', 'keripik', 'gorengan', 'rempeyek', 'krupuk',
            'dendeng', 'rendang'
        ]
        
        if medical_condition == 'diabetes':
            # Reject high carb foods (>30g carbs per serving)
            if carbs > 30:
                return False
            # Reject high calorie foods (>400 kcal)
            if calories > 400:
                return False
            # Reject foods with diabetes-unfriendly keywords
            if any(keyword in food_name_lower for keyword in high_carb_foods):
                return False
                
        elif medical_condition == 'hypertension':
            # Reject high sodium foods (>300mg sodium)
            if sodium > 300:
                return False
            # Reject processed/preserved foods
            if any(keyword in food_name_lower for keyword in high_sodium_foods):
                return False
                
        elif medical_condition == 'obesity':
            # Reject high calorie foods (>400 kcal)
            if calories > 400:
                return False
            # Reject high fat foods (>15g fat)
            if fat > 15:
                return False
            # Reject fried foods
            if any(keyword in food_name_lower for keyword in high_cal_fried_foods):
                return False
                
        return True

    def _calculate_nutritional_needs(self, user: User, goal: DietGoal) -> Dict:
        """Calculate nutritional needs based on user profile and diet goals."""
        height_m = user.height / 100
        
        if user.gender.upper() == 'M': 
            bmr = 88.362 + (13.397 * user.weight) + (4.799 * user.height) - (5.677 * user.age)
        elif user.gender.upper() == 'F':
            bmr = 447.593 + (9.247 * user.weight) + (3.098 * user.height) - (4.330 * user.age)
        else:
            bmr = 88.362 + (13.397 * user.weight) + (4.799 * user.height) - (5.677 * user.age)

        activity_multipliers = {
            'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55,
            'active': 1.725, 'very_active': 1.9 
        }
        
        activity_multiplier = activity_multipliers.get(user.activity_level, 1.2)
        tdee = bmr * activity_multiplier
        
        daily_calories = tdee
        if goal.target_weight < user.weight:
            daily_calories = tdee - 500
        elif goal.target_weight > user.weight:
            daily_calories = tdee + 300 
        
        medical_condition = getattr(goal, 'medical_condition', 'none')
        
        # Adjusted ratios for medical conditions
        carb_ratio, protein_ratio, fat_ratio = 0.50, 0.20, 0.30

        if medical_condition == 'diabetes':
            daily_calories *= 0.9
            carb_ratio, protein_ratio, fat_ratio = 0.30, 0.30, 0.40  # Lower carbs, higher protein
        elif medical_condition == 'hypertension':
            daily_calories *= 0.95
            carb_ratio, protein_ratio, fat_ratio = 0.45, 0.25, 0.30  # Moderate adjustment
        elif medical_condition == 'obesity':
            daily_calories *= 0.75  # More aggressive calorie reduction
            carb_ratio, protein_ratio, fat_ratio = 0.35, 0.35, 0.30  # Higher protein for satiety
        
        min_calories = 1200
        if user.gender.upper() == 'F' and daily_calories < 1200: 
            min_calories = 1000
        elif user.gender.upper() == 'M' and daily_calories < 1500: 
            min_calories = 1200
        daily_calories = max(min_calories, daily_calories)

        return {
            'daily_calories': daily_calories,
            'protein_g_per_day': (daily_calories * protein_ratio) / 4,
            'carbs_g_per_day': (daily_calories * carb_ratio) / 4,
            'fat_g_per_day': (daily_calories * fat_ratio) / 9,
            'medical_condition': medical_condition,
            'target_sodium_mg_per_meal': 200 if medical_condition == 'hypertension' else 600,
            'target_sugar_g_per_meal': 5 if medical_condition == 'diabetes' else 15,
            'max_calories_per_meal': 300 if medical_condition == 'obesity' else 500
        }

    def get_nutrition_recommendations(
        self, 
        user: User, 
        goal: DietGoal, 
        n_recommendations: int = 200,
        food_ids_to_consider: Optional[List[int]] = None
    ) -> List[Dict]:
        """Get nutrition recommendations based on user profile and diet goals."""
        if not user or not goal:
            return []
            
        nutritional_needs = self._calculate_nutritional_needs(user, goal)
        medical_condition = nutritional_needs['medical_condition']
        
        # Query foods with essential nutrients
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
        
        all_foods = foods_query.all()
        
        # Filter foods based on medical condition
        suitable_foods = [
            food for food in all_foods 
            if self._is_suitable_for_medical_condition(food, medical_condition)
        ]
        
        if not suitable_foods:
            return []

        recommendations = []
        
        # Adjust meal targets based on medical condition
        num_main_meals = 4 if medical_condition == 'obesity' else 3  # More frequent, smaller meals for obesity
        calories_per_meal = nutritional_needs['daily_calories'] / num_main_meals
        protein_per_meal = nutritional_needs['protein_g_per_day'] / num_main_meals
        carbs_per_meal = nutritional_needs['carbs_g_per_day'] / num_main_meals
        fat_per_meal = nutritional_needs['fat_g_per_day'] / num_main_meals

        # Apply stricter limits for medical conditions
        max_calories_per_meal = nutritional_needs.get('max_calories_per_meal', 500)
        max_carbs_per_meal = 20 if medical_condition == 'diabetes' else carbs_per_meal
        max_sodium_per_meal = nutritional_needs['target_sodium_mg_per_meal']

        for food in suitable_foods:
            # Skip foods that exceed medical limits
            if food.caloric_value > max_calories_per_meal:
                continue
            if medical_condition == 'diabetes' and food.carbohydrates > max_carbs_per_meal:
                continue
            if medical_condition == 'hypertension' and food.sodium and food.sodium > max_sodium_per_meal:
                continue

            # Calculate nutrition scores with medical condition penalties
            calorie_diff = abs(food.caloric_value - calories_per_meal)
            calorie_score = max(0, 1 - (calorie_diff / (calories_per_meal + 1e-6)))
            
            # Apply medical condition specific scoring
            if medical_condition == 'obesity':
                # Reward lower calorie foods more
                if food.caloric_value < calories_per_meal * 0.7:
                    calorie_score *= 1.5
                elif food.caloric_value > calories_per_meal * 1.2:
                    calorie_score *= 0.3
            
            protein_diff = abs(food.protein - protein_per_meal)
            protein_score = max(0, 1 - (protein_diff / (protein_per_meal + 1e-6)))
            
            # Boost protein for obesity (satiety)
            if medical_condition == 'obesity' and food.protein > protein_per_meal * 1.2:
                protein_score *= 1.3

            carb_diff = abs(food.carbohydrates - carbs_per_meal)
            carb_score = max(0, 1 - (carb_diff / (carbs_per_meal + 1e-6)))
            
            # Penalize high carbs for diabetes more severely
            if medical_condition == 'diabetes' and food.carbohydrates > carbs_per_meal * 0.8:
                carb_score *= 0.2

            fat_diff = abs(food.fat - fat_per_meal)
            fat_score = max(0, 1 - (fat_diff / (fat_per_meal + 1e-6)))
            
            # Penalize high fat for hypertension and obesity
            if medical_condition in ['hypertension', 'obesity'] and food.fat > fat_per_meal * 1.1:
                fat_score *= 0.4

            micronutrient_score_adj = self._calculate_micronutrient_score(food, nutritional_needs)

            total_score = (
                calorie_score * self.calorie_match_weight +
                protein_score * self.protein_match_weight +
                carb_score * self.carb_match_weight +
                fat_score * self.fat_match_weight +
                micronutrient_score_adj * self.micronutrient_adjustment_weight
            )
            total_score = max(0, min(1, total_score))

            recommendations.append({
                'food_id': food.id,
                'nutrition_score': float(total_score)
            })
        
        return sorted(recommendations, key=lambda x: x['nutrition_score'], reverse=True)[:n_recommendations]

    def _calculate_micronutrient_score(self, food: Food, nutritional_needs: Dict) -> float:
        """Calculate micronutrient score with enhanced medical condition consideration"""
        adjustment_score = 0.0
        medical_condition = nutritional_needs['medical_condition']
        
        if medical_condition == 'hypertension':
            if food.sodium is not None:
                target_sodium = nutritional_needs.get('target_sodium_mg_per_meal', 200)
                if food.sodium < target_sodium * 0.5:
                    adjustment_score += 0.5  # Reward very low sodium
                elif food.sodium > target_sodium:
                    adjustment_score -= 0.4  # Penalize high sodium
                    
            if food.potassium is not None:
                if food.potassium > 400:
                    adjustment_score += 0.4  # Reward high potassium
                elif food.potassium > 200:
                    adjustment_score += 0.2
                    
        elif medical_condition == 'diabetes':
            if food.dietary_fiber is not None:
                if food.dietary_fiber > 5:
                    adjustment_score += 0.5  # High fiber is very good
                elif food.dietary_fiber > 3:
                    adjustment_score += 0.3
                    
            # Penalize foods with likely added sugars
            food_name_lower = food.name.lower()
            if any(keyword in food_name_lower for keyword in ['manis', 'gula', 'sirup', 'madu']):
                adjustment_score -= 0.3
                
        elif medical_condition == 'obesity':
            # Reward high protein density
            if food.protein is not None and food.caloric_value is not None and food.caloric_value > 0:
                protein_density = food.protein / food.caloric_value * 100
                if protein_density > 20:
                    adjustment_score += 0.4  # Very high protein density
                elif protein_density > 15:
                    adjustment_score += 0.2
                    
            # Reward high fiber for satiety
            if food.dietary_fiber is not None:
                if food.dietary_fiber > 5:
                    adjustment_score += 0.3
                elif food.dietary_fiber > 3:
                    adjustment_score += 0.2
        
        # General micronutrients (reduced weight when medical condition is present)
        base_weight = 0.5 if medical_condition != 'none' else 1.0
        
        if food.iron is not None and food.iron > 2.5:
            adjustment_score += 0.1 * base_weight
        if food.calcium is not None and food.calcium > 150:
            adjustment_score += 0.1 * base_weight
        if food.zinc is not None and food.zinc > 1.5:
            adjustment_score += 0.05 * base_weight
        if food.vitamin_c is not None and food.vitamin_c > 15:
            adjustment_score += 0.05 * base_weight
            
        return max(-0.5, min(0.5, adjustment_score))