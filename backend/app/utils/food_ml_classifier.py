import joblib
import os
import pandas as pd
import pickle
import numpy as np
import sklearn
from sklearn.base import BaseEstimator

class VersionCompatibleLoader:
    @staticmethod
    def load(file_path):
        """Load a scikit-learn model with version compatibility handling"""
        try:
            # First attempt normal loading
            return joblib.load(file_path)
        except (ValueError, KeyError, pickle.UnpicklingError) as e:
            # Handle node array structure incompatibility specific to sklearn tree-based models
            if "node array" in str(e) and "incompatible dtype" in str(e):
                print(f"Handling version compatibility for {file_path}")
                
                # Create a custom unpickler to modify the tree structure
                class CustomUnpickler(pickle.Unpickler):
                    def find_class(self, module, name):
                        return super().find_class(module, name)

                with open(file_path, 'rb') as f:
                    unpickler = CustomUnpickler(f)
                    model = unpickler.load()

                # Handle tree-based models specifically
                if hasattr(model, 'tree_') or (hasattr(model, 'estimators_') and len(model.estimators_) > 0):
                    # For RandomForest models
                    if hasattr(model, 'estimators_'):
                        for i, estimator in enumerate(model.estimators_):
                            if hasattr(estimator, 'tree_'):
                                tree = estimator.tree_
                                # Create the missing_go_to_left field with default values (all False)
                                if not hasattr(tree, 'missing_go_to_left'):
                                    tree.missing_go_to_left = np.zeros(tree.node_count, dtype=np.bool_)
                    # For single tree models
                    elif hasattr(model, 'tree_'):
                        tree = model.tree_
                        if not hasattr(tree, 'missing_go_to_left'):
                            tree.missing_go_to_left = np.zeros(tree.node_count, dtype=np.bool_)
                
                return model
            else:
                # Fall back to creating a new model if other issues occur
                if 'food_status' in file_path:
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(n_estimators=100, random_state=42)
                    print(f"Created new RandomForestClassifier as fallback for {file_path}")
                    return model
                elif 'meal_type' in file_path:
                    from sklearn.ensemble import RandomForestClassifier
                    model = RandomForestClassifier(n_estimators=150, random_state=42)
                    print(f"Created new RandomForestClassifier as fallback for {file_path}")
                    return model
                else:
                    # Re-raise if we can't handle it
                    raise

class FoodMLClassifier:
    def __init__(self):
        # Try multiple possible model locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'model'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'model'),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'model_output'),
            'model_output'
        ]
        
        # Find the first valid path that has the models
        model_path = None
        for path in possible_paths:
            if os.path.exists(os.path.join(path, 'food_status_classifier.joblib')):
                model_path = path
                print(f"Found models in: {os.path.abspath(path)}")
                break
                
        if not model_path:
            print("Warning: Could not find model files in any expected location")
            self.food_status_classifier = None
            self.food_status_encoder = None
            self.meal_type_classifier = None
            self.meal_type_encoder = None
            return
        
        try:
            # Try to load the food status classifier model and label encoder
            self.food_status_classifier = VersionCompatibleLoader.load(os.path.join(model_path, 'food_status_classifier.joblib'))
            self.food_status_encoder = joblib.load(os.path.join(model_path, 'food_status_label_encoder.joblib'))
            
            # Try to load the meal type classifier model and label encoder
            self.meal_type_classifier = VersionCompatibleLoader.load(os.path.join(model_path, 'meal_type_classifier.joblib'))
            self.meal_type_encoder = joblib.load(os.path.join(model_path, 'meal_type_label_encoder.joblib'))
            
            print("Successfully loaded all ML models for food classification")
        except Exception as e:
            print(f"Error loading ML models: {e}")
            # Set fallback models
            self.food_status_classifier = None
            self.food_status_encoder = None
            self.meal_type_classifier = None
            self.meal_type_encoder = None
        
        # Define keyword dictionaries in Indonesian (match with script_model.py)
        self.breakfast_keywords = [
            'telur', 'roti', 'bubur', 'oatmeal', 'sereal', 'granola',
            'susu', 'yogurt', 'keju', 'pancake', 'wafel', 'kue',
            'pisang', 'apel', 'jeruk', 'buah', 'kopi', 'teh',
            'lontong', 'ketupat', 'tape', 'ketan'
        ]
        
        self.lunch_dinner_keywords = [
            'nasi', 'mie', 'bihun', 'pasta', 'soup', 'soto', 'sop',
            'gulai', 'kari', 'bakso', 'sayur', 'tumis', 'ayam',
            'daging', 'ikan', 'udang', 'tahu', 'tempe', 'goreng',
            'bakar', 'pepes', 'rica', 'rendang', 'geprek', 'lalapan',
            'gado-gado', 'ketoprak', 'rujak', 'sate', 'sambal',
            'terong', 'kangkung', 'capcay', 'lodeh'
        ]
        
        self.snack_keywords = [
            'kue', 'coklat', 'permen', 'biskuit', 'keripik', 'kerupuk',
            'buah', 'jelly', 'wafer', 'cookies', 'pudding', 'es',
            'jus', 'risoles', 'gorengan', 'martabak', 'pisang goreng',
            'bakwan', 'onde-onde', 'klepon', 'lemper', 'lumpia',
            'bolu', 'brownie', 'batagor', 'siomay', 'seblak', 'cilok'
        ]
        
    def predict_food_status(self, food_name, calories, proteins, fat, carbs):
        """
        Predict if a food is raw or processed
        Returns: 'Mentah' or 'Olahan'
        """
        # Prepare input data - Fix: changed 'cleaned_name' to 'name_cleaned'
        X = pd.DataFrame({
            'name_cleaned': [food_name.lower()],
            'calories': [float(calories)],
            'proteins': [float(proteins)],
            'fat': [float(fat)],
            'carbohydrate': [float(carbs)]
        })
        
        # Try to make prediction, fall back to default if model fails
        try:
            if self.food_status_classifier and self.food_status_encoder:
                prediction = self.food_status_classifier.predict(X)
                return self.food_status_encoder.inverse_transform(prediction)[0]
            raise ValueError("Model not available")
        except Exception as e:
            print(f"Error predicting food status: {e}")
            # Fallback to a simple heuristic
            if float(calories) < 150 and float(carbs) > float(proteins) * 2:
                return 'Mentah'  # Raw foods tend to have lower calories and higher carbs
            return 'Olahan'
        
    def predict_meal_type(self, food_name, calories, proteins, fat, carbs, food_status):
        """
        Predict the meal type for a food using the correct feature set
        Returns: 'Sarapan', 'Makan Siang', 'Makan Malam', or 'Cemilan'
        """
        # Convert to float
        calories = float(calories) if calories else 0
        proteins = float(proteins) if proteins else 0
        fat = float(fat) if fat else 0
        carbs = float(carbs) if carbs else 0
        
        # Calculate nutrient ratios (match script_model.py implementation)
        total_cal = max(1, calories)  # Avoid division by zero
        protein_ratio = (proteins * 4 / total_cal) * 100
        fat_ratio = (fat * 9 / total_cal) * 100
        carb_ratio = (carbs * 4 / total_cal) * 100
        
        # Generate keyword features
        name_lower = food_name.lower()
        is_breakfast_keyword = int(any(kw in name_lower for kw in self.breakfast_keywords))
        is_lunch_dinner_keyword = int(any(kw in name_lower for kw in self.lunch_dinner_keywords))
        is_snack_keyword = int(any(kw in name_lower for kw in self.snack_keywords))
        
        # Create input dataframe with the exact features expected by the model
        X = pd.DataFrame({
            'calories': [calories],
            'protein_ratio': [protein_ratio], 
            'fat_ratio': [fat_ratio],
            'carb_ratio': [carb_ratio],
            'is_breakfast_keyword': [is_breakfast_keyword],
            'is_lunch_dinner_keyword': [is_lunch_dinner_keyword],
            'is_snack_keyword': [is_snack_keyword]
        })
        
        # Try to make prediction, fallback to heuristic if model fails
        try:
            if self.meal_type_classifier and self.meal_type_encoder:
                prediction = self.meal_type_classifier.predict(X)
                return self.meal_type_encoder.inverse_transform(prediction)[0]
            raise ValueError("Model not available")
        except Exception as e:
            print(f"Error predicting meal type: {e}")
            
            # Fallback to heuristic classification using the same logic as script_model.py
            return self.predict_meal_type_heuristic(food_name, calories, proteins, fat, carbs, food_status)
            
    def predict_meal_type_heuristic(self, food_name, calories, proteins, fat, carbs, food_status=None):
        """
        Predict meal type using heuristics when model is not available or fails
        This matches the implementation in script_model.py
        """
        # Calculate derived features (same as in script_model.py)
        total_cal = max(1, calories)  # Avoid division by zero
        protein_ratio = (proteins * 4 / total_cal) * 100
        carb_ratio = (carbs * 4 / total_cal) * 100
        fat_ratio = (fat * 9 / total_cal) * 100
        
        name_lower = food_name.lower()
        
        # Check for breakfast keywords
        if any(kw in name_lower for kw in self.breakfast_keywords) and calories < 450:
            return 'Sarapan'  # Breakfast
        
        # Check for snack keywords
        if any(kw in name_lower for kw in self.snack_keywords) and calories < 300:
            return 'Cemilan'  # Snack
        
        # Check for lunch/dinner keywords
        if any(kw in name_lower for kw in self.lunch_dinner_keywords):
            if calories <= 350 and calories > 150:
                return 'Makan Siang'  # Lunch
            elif calories > 350:
                return 'Makan Malam'  # Dinner
        
        # Apply calorie and macronutrient based rules
        if calories < 150 or (carb_ratio > 50 and calories < 250):
            return 'Cemilan'  # Snack
        elif protein_ratio > 25 and calories > 400:
            return 'Makan Malam'  # Dinner
        elif protein_ratio > 15 and 200 <= calories < 450:
            return 'Makan Siang'  # Lunch
        elif carb_ratio > 40 and 150 <= calories < 350:
            return 'Sarapan'  # Breakfast
        elif calories >= 450:
            return 'Makan Malam'  # Dinner
        elif 200 <= calories < 350:
            return 'Makan Siang'  # Lunch
        else:
            return 'Makan Siang'  # Default case