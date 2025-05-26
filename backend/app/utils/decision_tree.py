from typing import Dict, List
from app.models.user import User
from app.models.recommendation import DietGoal
from app.models.food import Food

class NutritionDecisionTree:
    def __init__(self):
        # Adjusted weights for better balance
        self.calorie_match_weight = 0.25
        self.protein_match_weight = 0.25
        self.carb_match_weight = 0.20
        self.fat_match_weight = 0.15
        self.micronutrient_adjustment_weight = 0.15

    def _calculate_nutritional_needs(self, user: User, goal: DietGoal) -> Dict:
        """Calculate nutritional needs based on user profile and diet goals."""
        height_m = user.height / 100
        bmi = user.weight / (height_m ** 2)
        
        # Calculate BMR using Mifflin-St Jeor Equation
        if user.gender == 'male':
            bmr = 88.362 + (13.397 * user.weight) + (4.799 * user.height) - (5.677 * user.age)
        else:
            bmr = 447.593 + (9.247 * user.weight) + (3.098 * user.height) - (4.330 * user.age)
        
        # Activity level multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725
        }
        
        tdee = bmr * activity_multipliers.get(user.activity_level, 1.2)
        
        # Adjust calories based on goal
        if goal.target_weight < user.weight:  # Weight loss
            daily_calories = tdee - 500  # 1 lb per week
        elif goal.target_weight > user.weight:  # Weight gain
            daily_calories = tdee + 300
        else:  # Maintenance
            daily_calories = tdee
        
        # Adjust for medical conditions
        medical_condition = getattr(goal, 'medical_condition', 'none')
        
        if medical_condition == 'diabetes':
            daily_calories *= 0.9  # Slightly reduce calories
            carb_ratio = 0.35  # Lower carbs
            protein_ratio = 0.25
            fat_ratio = 0.40
        elif medical_condition == 'hypertension':
            daily_calories *= 0.95
            carb_ratio = 0.50
            protein_ratio = 0.25
            fat_ratio = 0.25
        elif medical_condition == 'obesity':
            daily_calories *= 0.85  # More aggressive deficit
            carb_ratio = 0.40
            protein_ratio = 0.30  # Higher protein
            fat_ratio = 0.30
        else:  # Normal
            carb_ratio = 0.50
            protein_ratio = 0.20
            fat_ratio = 0.30
        
        return {
            'daily_calories': max(1200, daily_calories),  # Minimum 1200 calories
            'protein_g_per_day': (daily_calories * protein_ratio) / 4,
            'carbs_g_per_day': (daily_calories * carb_ratio) / 4,
            'fat_g_per_day': (daily_calories * fat_ratio) / 9,
            'medical_condition': medical_condition,
            'target_sodium_mg_per_meal': 700 if medical_condition == 'hypertension' else 1000,
            'target_sugar_g_per_meal': 10 if medical_condition == 'diabetes' else 20
        }

    def _calculate_micronutrient_score(self, food: Food, nutritional_needs: Dict) -> float:
        """Calculate score adjustment based on micronutrients and medical conditions."""
        adjustment_score = 0.0
        num_relevant_micronutrients = 0
        
        medical_condition = nutritional_needs['medical_condition']
        
        if medical_condition == 'hypertension':
            # Sodium scoring
            if food.sodium is not None:
                num_relevant_micronutrients += 1
                target_sodium = nutritional_needs.get('target_sodium_mg_per_meal', 700)
                if food.sodium < target_sodium * 0.3:  # Very low sodium
                    adjustment_score += 0.4
                elif food.sodium < target_sodium * 0.6:  # Low sodium
                    adjustment_score += 0.2
                elif food.sodium > target_sodium * 1.5:  # High sodium
                    adjustment_score -= 0.3
            
            # Potassium scoring (good for hypertension)
            if food.potassium is not None:
                num_relevant_micronutrients += 1
                if food.potassium > 300:  # High potassium
                    adjustment_score += 0.3
                elif food.potassium > 150:  # Moderate potassium
                    adjustment_score += 0.15
                    
        elif medical_condition == 'diabetes':
            # Fiber scoring (good for diabetes)
            if food.dietary_fiber is not None:
                num_relevant_micronutrients += 1
                if food.dietary_fiber > 5:  # High fiber
                    adjustment_score += 0.4
                elif food.dietary_fiber > 2:  # Moderate fiber
                    adjustment_score += 0.2
            
            # Sugar content (if available in future)
            # Lower sugar foods get bonus points
            
        elif medical_condition == 'obesity':
            # Favor foods with better nutrient density
            if food.protein is not None and food.caloric_value is not None:
                if food.caloric_value > 0:
                    protein_density = food.protein / food.caloric_value * 100
                    if protein_density > 0.15:  # High protein density
                        adjustment_score += 0.3
                    elif protein_density > 0.10:
                        adjustment_score += 0.15
                        
            # Fiber bonus for satiety
            if food.dietary_fiber is not None:
                num_relevant_micronutrients += 1
                if food.dietary_fiber > 4:
                    adjustment_score += 0.2
                elif food.dietary_fiber > 2:
                    adjustment_score += 0.1
        
        # General micronutrient bonuses
        if food.iron is not None and food.iron > 2:
            adjustment_score += 0.1
        if food.calcium is not None and food.calcium > 100:
            adjustment_score += 0.1
        if food.zinc is not None and food.zinc > 1:
            adjustment_score += 0.05
            
        # Normalize score
        if num_relevant_micronutrients > 0:
            return min(1.0, adjustment_score)
        else:
            return 0.0

    def get_nutrition_recommendations(self, user: User, goal: DietGoal, n_recommendations: int = 200) -> List[Dict]:
        """Get nutrition recommendations based on user profile and diet goals."""
        if not user or not goal:
            print("Warning: Invalid user or DietGoal for get_nutrition_recommendations.")
            return []
            
        nutritional_needs = self._calculate_nutritional_needs(user, goal)
        
        # Get all foods
        all_foods = Food.query.filter(
            Food.caloric_value.isnot(None),
            Food.protein.isnot(None),
            Food.carbohydrates.isnot(None),
            Food.fat.isnot(None)
        ).all()
        
        if not all_foods:
            print("No food data in database.")
            return []

        recommendations = []
        
        # Calculate target nutrients per meal (assuming 3 main meals)
        calories_per_meal = nutritional_needs['daily_calories'] / 3
        protein_per_meal = nutritional_needs['protein_g_per_day'] / 3
        carbs_per_meal = nutritional_needs['carbs_g_per_day'] / 3
        fat_per_meal = nutritional_needs['fat_g_per_day'] / 3

        for food in all_foods:
            # Skip foods with missing essential data
            if any(val is None for val in [food.caloric_value, food.protein, food.carbohydrates, food.fat]):
                continue

            # 1. Calorie matching score
            calorie_diff_ratio = abs(food.caloric_value - calories_per_meal) / calories_per_meal
            calorie_score = max(0, 1 - calorie_diff_ratio)
            
            # Penalty for excessive calories
            if food.caloric_value > calories_per_meal * 1.5:
                calorie_score *= 0.5
            # Bonus for appropriate calorie range
            elif 0.7 <= food.caloric_value / calories_per_meal <= 1.2:
                calorie_score = min(1.0, calorie_score + 0.2)

            # 2. Protein matching score
            protein_diff_ratio = abs(food.protein - protein_per_meal) / protein_per_meal if protein_per_meal > 0 else 1
            protein_score = max(0, 1 - protein_diff_ratio)
            
            # Bonus for adequate protein
            if food.protein >= protein_per_meal * 0.8:
                protein_score = min(1.0, protein_score + 0.3)

            # 3. Carbohydrate matching score
            carb_diff_ratio = abs(food.carbohydrates - carbs_per_meal) / carbs_per_meal if carbs_per_meal > 0 else 1
            carb_score = max(0, 1 - carb_diff_ratio)
            
            # Medical condition adjustments
            if nutritional_needs['medical_condition'] == 'diabetes':
                if food.carbohydrates > carbs_per_meal * 1.3:
                    carb_score *= 0.6  # Stronger penalty for high carbs
                elif food.carbohydrates < carbs_per_meal * 0.7:
                    carb_score = min(1.0, carb_score + 0.2)  # Bonus for lower carbs

            # 4. Fat matching score
            fat_diff_ratio = abs(food.fat - fat_per_meal) / fat_per_meal if fat_per_meal > 0 else 1
            fat_score = max(0, 1 - fat_diff_ratio)
            
            # Medical condition adjustments for fat
            if nutritional_needs['medical_condition'] in ['hypertension', 'obesity']:
                if food.fat > fat_per_meal * 1.2:
                    fat_score *= 0.7

            # 5. Micronutrient adjustment score
            micronutrient_score = self._calculate_micronutrient_score(food, nutritional_needs)

            # Calculate total score
            total_score = (
                calorie_score * self.calorie_match_weight +
                protein_score * self.protein_match_weight +
                carb_score * self.carb_match_weight +
                fat_score * self.fat_match_weight +
                micronutrient_score * self.micronutrient_adjustment_weight
            )
            
            # Ensure score is between 0 and 1
            total_score = max(0, min(1, total_score))

            recommendations.append({
                'food_id': food.id,
                'nutrition_score': float(total_score)
            })
        
        # Sort by score and return top recommendations
        return sorted(recommendations, key=lambda x: x['nutrition_score'], reverse=True)[:n_recommendations]