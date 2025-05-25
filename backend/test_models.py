from app.utils.food_ml_classifier import FoodMLClassifier
import pandas as pd
import os

def test_meal_classification():
    """Test if our meal classifier works correctly with various foods"""
    # Create the classifier
    classifier = FoodMLClassifier()
    
    # Create test samples including breakfast, lunch, dinner, and snack items
    test_foods = [
        # Breakfast items
        {"name": "Telur dadar", "calories": 150, "proteins": 12, "fat": 10, "carbs": 1},
        {"name": "Roti tawar", "calories": 180, "proteins": 5, "fat": 3, "carbs": 30},
        {"name": "Bubur ayam", "calories": 250, "proteins": 10, "fat": 6, "carbs": 35},
        {"name": "Sereal dengan susu", "calories": 200, "proteins": 6, "fat": 4, "carbs": 32},
        
        # Lunch items
        {"name": "Nasi goreng", "calories": 400, "proteins": 15, "fat": 12, "carbs": 60},
        {"name": "Gado-gado", "calories": 300, "proteins": 10, "fat": 15, "carbs": 30},
        {"name": "Mie goreng", "calories": 380, "proteins": 12, "fat": 14, "carbs": 50},
        
        # Dinner items
        {"name": "Ayam bakar", "calories": 350, "proteins": 35, "fat": 18, "carbs": 5},
        {"name": "Ikan goreng", "calories": 300, "proteins": 28, "fat": 16, "carbs": 10},
        {"name": "Rendang sapi", "calories": 520, "proteins": 45, "fat": 35, "carbs": 7},
        
        # Snacks
        {"name": "Pisang", "calories": 90, "proteins": 1, "fat": 0.3, "carbs": 22},
        {"name": "Keripik singkong", "calories": 120, "proteins": 1, "fat": 6, "carbs": 15},
        {"name": "Es teh manis", "calories": 90, "proteins": 0, "fat": 0, "carbs": 22},
    ]
    
    results = []
    for food in test_foods:
        # First predict food status
        food_status = classifier.predict_food_status(
            food["name"], food["calories"], food["proteins"], food["fat"], food["carbs"]
        )
        
        # Then predict meal type
        meal_type = classifier.predict_meal_type(
            food["name"], food["calories"], food["proteins"], 
            food["fat"], food["carbs"], food_status
        )
        
        results.append({
            "name": food["name"],
            "calories": food["calories"],
            "proteins": food["proteins"],
            "fat": food["fat"],
            "carbs": food["carbs"],
            "food_status": food_status,
            "meal_type": meal_type
        })
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(results)
    print("\nMeal Type Classification Results:")
    print(df)
    
    # Check distribution of meal types
    print("\nMeal Type Distribution:")
    print(df["meal_type"].value_counts())
    
    # Check if we have breakfast items
    breakfast_count = len(df[df["meal_type"] == "Sarapan"])
    print(f"\nBreakfast items found: {breakfast_count}")
    if breakfast_count == 0:
        print("WARNING: No breakfast items were classified correctly!")
    
    return df

if __name__ == "__main__":
    test_meal_classification()