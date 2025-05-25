-- Buat database
CREATE DATABASE IF NOT EXISTS diet_recommendation;
USE diet_recommendation;

-- Tabel Users
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    age INT,
    weight FLOAT,
    height FLOAT,
    gender ENUM('M', 'F'),
    activity_level ENUM('sedentary', 'light', 'moderate', 'active', 'very_active'),
    medical_condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabel Food Preferences
CREATE TABLE food_preferences (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    preference_type ENUM('vegetarian', 'vegan', 'halal', 'kosher'),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Food Allergies
CREATE TABLE food_allergies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    allergy_name VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Foods
CREATE TABLE foods (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    caloric_value FLOAT,
    fat FLOAT,
    saturated_fats FLOAT,
    monounsaturated_fats FLOAT,
    polyunsaturated_fats FLOAT,
    carbohydrates FLOAT,
    sugars FLOAT,
    protein FLOAT,
    dietary_fiber FLOAT,
    cholesterol FLOAT,
    sodium FLOAT,
    water FLOAT,
    vitamin_a FLOAT,
    vitamin_b1 FLOAT,
    vitamin_b11 FLOAT,
    vitamin_b12 FLOAT,
    vitamin_b2 FLOAT,
    vitamin_b3 FLOAT,
    vitamin_b5 FLOAT,
    vitamin_b6 FLOAT,
    vitamin_c FLOAT,
    vitamin_d FLOAT,
    vitamin_e FLOAT,
    vitamin_k FLOAT,
    calcium FLOAT,
    copper FLOAT,
    iron FLOAT,
    magnesium FLOAT,
    manganese FLOAT,
    phosphorus FLOAT,
    potassium FLOAT,
    selenium FLOAT,
    zinc FLOAT,
    nutrition_density FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabel Diet Goals
CREATE TABLE diet_goals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    goal_type ENUM('weight_loss', 'muscle_gain', 'maintenance', 'diabetes_friendly'),
    target_weight FLOAT,
    target_date DATE,
    status ENUM('active', 'completed', 'abandoned') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel Recommendations
CREATE TABLE recommendations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    food_id INT,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack'),
    recommendation_date DATE,
    is_consumed BOOLEAN DEFAULT FALSE,
    rating INT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (food_id) REFERENCES foods(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
