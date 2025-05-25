from sklearn.tree import DecisionTreeClassifier
import numpy as np
from typing import Dict, List
from app.models.food import Food
from app.models.user import User
from app.models.recommendation import DietGoal


class NutritionDecisionTree:
    def __init__(self):
        self.classifier = DecisionTreeClassifier(
            criterion='entropy',
            max_depth=5,
            min_samples_split=20,
            min_samples_leaf=10
        )

    def _calculate_nutritional_needs(self, user: User, goal: DietGoal) -> Dict:
        """Calculate nutritional needs based on profile and weight loss goal"""
        # Calculate BMR
        if user.gender == 'M':
            bmr = 88.362 + (13.397 * user.weight) + \
                (4.799 * user.height) - (5.677 * user.age)
        else:
            bmr = 447.593 + (9.247 * user.weight) + \
                (3.098 * user.height) - (4.330 * user.age)

        # Activity multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9
        }

        daily_calories = bmr * activity_multipliers[user.activity_level]
        
        # For weight loss, create a calorie deficit of 20%
        daily_calories *= 0.8
        
        # Adjust macronutrient distribution based on medical condition
        if goal.medical_condition == 'diabetes':
            # Lower carbs, higher protein for diabetes
            macro_ratio = {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30}
        elif goal.medical_condition == 'hypertension':
            # Lower fat, moderate protein for hypertension
            macro_ratio = {'protein': 0.25, 'carbs': 0.55, 'fat': 0.20}
        elif goal.medical_condition == 'obesity':
            # Higher protein, lower carbs for obesity
            macro_ratio = {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25}
        else:  # Default weight loss
            macro_ratio = {'protein': 0.30, 'carbs': 0.45, 'fat': 0.25}

        return {
            'daily_calories': daily_calories,
            'protein': (daily_calories * macro_ratio['protein']) / 4,  # 4 cal/g
            'carbs': (daily_calories * macro_ratio['carbs']) / 4,      # 4 cal/g
            'fat': (daily_calories * macro_ratio['fat']) / 9,          # 9 cal/g
            'medical_condition': goal.medical_condition
        }

    def _create_food_features(self, food: Food, nutritional_needs: Dict) -> np.ndarray:
        """Create feature vector for the food item based on nutritional profile"""
        features = np.zeros(5)  # Reduced features to focus on macronutrients only

        # Calorie matching (per meal portion)
        meal_portion = nutritional_needs['daily_calories'] / 3
        calorie_ratio = food.caloric_value / meal_portion
        features[0] = max(0, 1 - abs(1 - calorie_ratio))

        # Macro nutrient matching
        protein_ratio = food.protein / (nutritional_needs['protein'] / 3)
        carb_ratio = food.carbohydrates / (nutritional_needs['carbs'] / 3)
        fat_ratio = food.fat / (nutritional_needs['fat'] / 3)

        features[1] = max(0, 1 - abs(1 - protein_ratio))
        features[2] = max(0, 1 - abs(1 - carb_ratio))
        features[3] = max(0, 1 - abs(1 - fat_ratio))

        # Medical condition specific scoring
        if nutritional_needs['medical_condition'] == 'diabetes':
            # For diabetes, prefer foods with lower carbs
            features[4] = 1 if (food.carbohydrates < (nutritional_needs['carbs'] / 3) * 0.8) else 0
        elif nutritional_needs['medical_condition'] == 'hypertension':
            # For hypertension, prefer foods with lower fat
            features[4] = 1 if (food.fat < (nutritional_needs['fat'] / 3) * 0.8) else 0
        elif nutritional_needs['medical_condition'] == 'obesity':
            # For obesity, prefer foods with higher protein and moderate fat
            features[4] = 1 if (food.protein > (nutritional_needs['protein'] / 3) * 1.2) and \
                              (food.fat < (nutritional_needs['fat'] / 3) * 1.1) else 0
        else:
            # For general weight loss
            features[4] = 1 if (food.protein >= (nutritional_needs['protein'] / 3) * 0.9) and \
                              (food.caloric_value < meal_portion) else 0

        return features

    def get_nutrition_recommendations(self, user: User, goal: DietGoal, n_recommendations: int = 10) -> List[Dict]:
        """Get nutrition recommendations based on user profile and dietary goals"""
        nutritional_needs = self._calculate_nutritional_needs(user, goal)
        
        # Get only Indonesian foods
        foods = Food.query.all()

        recommendations = []
        for food in foods:
            features = self._create_food_features(food, nutritional_needs)
            
            # Calculate weighted score directly
            score = (
                features[0] * 0.30 +  # Calorie match
                features[1] * 0.25 +  # Protein match
                features[2] * 0.15 +  # Carb match
                features[3] * 0.15 +  # Fat match
                features[4] * 0.15    # Medical condition specific
            )

            recommendations.append({
                'food_id': food.id,
                'nutrition_score': float(score)
            })
        
        # Sort and return top recommendations
        return sorted(recommendations, key=lambda x: x['nutrition_score'], reverse=True)[:n_recommendations]