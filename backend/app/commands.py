import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User # Pastikan User diimpor jika seed_users_command masih digunakan
from app.models.recommendation import DietGoal, Recommendation # Pastikan DietGoal dan Recommendation diimpor
from datetime import datetime, timedelta
import random
from sqlalchemy import func
import csv
import os
from app.models.food import Food
from app.utils.food_classifier import FoodClassifier # Jika masih digunakan
from app.utils.decision_tree import NutritionDecisionTree
import pandas as pd
import numpy as np

# Definisi KJ_TO_KCAL tidak diperlukan lagi jika energi sudah dalam kkal
# KJ_TO_KCAL = 1 / 4.184 

@click.command('seed-users')
@click.option('--count', default=10, help='Number of users to create')
@with_appcontext
def seed_users_command(count):
    """Seed database with sample users"""
    try:
        max_user_id = db.session.query(func.max(User.id)).scalar() or 0
        for i in range(count):
            user = User(
                username=f'testuser{max_user_id + i + 1}',
                email=f'test{max_user_id + i + 1}@example.com',
                age=random.randint(18, 80),
                weight=random.uniform(45.0, 120.0),
                height=random.uniform(150.0, 190.0),
                gender=random.choice(['M', 'F']),
                activity_level=random.choice(
                    ['sedentary', 'light', 'moderate', 'active', 'very_active']),
                medical_condition=random.choice(
                    ['none', 'diabetes', 'hypertension', 'obesity'])
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush()  

            goal = DietGoal(
                user_id=user.id,
                target_weight=random.uniform(50.0, 90.0),
                target_date=(datetime.now() +
                             timedelta(days=random.randint(30, 365))).date(),
                medical_condition=random.choice(
                    ['none', 'diabetes', 'hypertension', 'obesity']),
                status='active'
            )
            db.session.add(goal)
        db.session.commit()
        click.echo(f'Created {count} test users with weight loss goals')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating test users: {str(e)}')


@click.command('import-nutrition-data') # Nama perintah diubah agar lebih generik
@click.option('--source', default='dataset-diet', help='Source directory for data files. Default: dataset-diet')
@click.option('--filename', default='dataset_nutrisi_kurasi_final.csv', help='Filename of the CSV data. Default: dataset_nutrisi_kurasi_final')
@click.option('--classify', default=True, type=bool, help='Run food classifier after import. Default: True')
@with_appcontext
def import_nutrition_data_command(source, filename, classify):
    """Import nutrition data from the specified CSV dataset."""
    try:
        # Hapus semua data rekomendasi yang terkait dengan makanan yang ada
        # Ini penting jika ID makanan berubah atau makanan lama dihapus
        num_deleted_recs = Recommendation.query.delete()
        db.session.commit()
        click.echo(f"Deleted {num_deleted_recs} existing recommendation records.")

        # Hapus semua data makanan yang ada untuk menghindari duplikasi dan memastikan data segar
        num_deleted_foods = Food.query.delete()
        db.session.commit()
        click.echo(f"Deleted {num_deleted_foods} existing food records.")

        script_dir = os.path.dirname(os.path.abspath(__file__)) # e.g., c:\project\diet-recommendation\backend\app
        base_dir_for_source = os.path.abspath(os.path.join(script_dir, '..')) # e.g., c:\project\diet-recommendation\backend
        file_path = os.path.join(base_dir_for_source, source, filename)
        
        click.echo(f"Attempting to open file at: {file_path}")
        
        count = 0
        
        # Indeks kolom berdasarkan file dataset_nutrisi_kurasi_final_v1.csv
        # kode,nama_makanan,energi_kal,protein_g,lemak_g,karbohidrat_g,serat_g,kalsium_mg,
        # fosfor_mg,besi_mg,natrium_mg,kalium_mg,tembaga_mg,seng_mg,retinol_mcg,thiamin_mg,
        # riboflavin_mg,niasin_mg,vitamin_c_mg,status_makanan,kelompok_makanan,meal_type
        
        IDX_KODE = 0
        IDX_NAMA_MAKANAN = 1
        IDX_ENERGI_KAL = 2
        IDX_PROTEIN_G = 3
        IDX_LEMAK_G = 4
        IDX_KARBOHIDRAT_G = 5
        IDX_SERAT_G = 6
        IDX_KALSIUM_MG = 7
        IDX_FOSFOR_MG = 8
        IDX_BESI_MG = 9
        IDX_NATRIUM_MG = 10
        IDX_KALIUM_MG = 11
        IDX_TEMBAGA_MG = 12
        IDX_SENG_MG = 13
        IDX_RETINOL_MCG = 14
        IDX_THIAMIN_MG = 15
        IDX_RIBOFLAVIN_MG = 16
        IDX_NIASIN_MG = 17
        IDX_VITAMIN_C_MG = 18
        IDX_STATUS_MAKANAN = 19
        IDX_KELOMPOK_MAKANAN = 20
        IDX_MEAL_TYPE = 21
        
        EXPECTED_COLUMNS = 22 # Jumlah kolom yang diharapkan

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader) 
            click.echo(f"CSV Header: {header}")

            if len(header) < EXPECTED_COLUMNS:
                click.echo(f"Error: CSV file '{filename}' does not have the expected number of columns (at least {EXPECTED_COLUMNS}). Found {len(header)} columns.")
                click.echo(f"Expected header like: kode,nama_makanan,... (total {EXPECTED_COLUMNS})")
                return

            for row_number, row in enumerate(reader, 1):
                try:
                    if not any(field.strip() for field in row): # Lewati baris kosong
                        click.echo(f"Skipping empty row {row_number}.")
                        continue

                    if len(row) < EXPECTED_COLUMNS:
                        click.echo(f"Skipping row {row_number} due to insufficient columns ({len(row)} found, {EXPECTED_COLUMNS} expected): {row}")
                        continue

                    food_code_val = row[IDX_KODE].strip()
                    name_val = row[IDX_NAMA_MAKANAN].strip()
                    
                    if not name_val:
                        click.echo(f"Skipping row {row_number} due to empty food name.")
                        continue
                        
                    def safe_float_conversion(value_str, default=None): # Default ke None jika tidak bisa konversi
                        if value_str is None or str(value_str).strip() == '':
                            return default
                        try:
                            cleaned_value_str = str(value_str).replace(',', '.').strip()
                            return float(cleaned_value_str)
                        except ValueError:
                            # click.echo(f"Warning: Could not convert '{value_str}' to float for food '{name_val}'. Using default {default}.")
                            return default
                    
                    # Membuat instance Food
                    food = Food(
                        food_code=food_code_val if food_code_val else None,
                        name=name_val,
                        caloric_value=safe_float_conversion(row[IDX_ENERGI_KAL]),
                        protein=safe_float_conversion(row[IDX_PROTEIN_G]),
                        fat=safe_float_conversion(row[IDX_LEMAK_G]),
                        carbohydrates=safe_float_conversion(row[IDX_KARBOHIDRAT_G]),
                        dietary_fiber=safe_float_conversion(row[IDX_SERAT_G]),
                        calcium=safe_float_conversion(row[IDX_KALSIUM_MG]),
                        phosphorus=safe_float_conversion(row[IDX_FOSFOR_MG]),
                        iron=safe_float_conversion(row[IDX_BESI_MG]),
                        sodium=safe_float_conversion(row[IDX_NATRIUM_MG]),
                        potassium=safe_float_conversion(row[IDX_KALIUM_MG]),
                        copper=safe_float_conversion(row[IDX_TEMBAGA_MG]),
                        zinc=safe_float_conversion(row[IDX_SENG_MG]),
                        retinol_mcg=safe_float_conversion(row[IDX_RETINOL_MCG]),
                        thiamin_mg=safe_float_conversion(row[IDX_THIAMIN_MG]), # Menggunakan nama field baru
                        riboflavin_mg=safe_float_conversion(row[IDX_RIBOFLAVIN_MG]), # Menggunakan nama field baru
                        niacin_mg=safe_float_conversion(row[IDX_NIASIN_MG]),
                        vitamin_c=safe_float_conversion(row[IDX_VITAMIN_C_MG]),
                        food_status=row[IDX_STATUS_MAKANAN].strip() if row[IDX_STATUS_MAKANAN] else None,
                        food_group=row[IDX_KELOMPOK_MAKANAN].strip() if row[IDX_KELOMPOK_MAKANAN] else None,
                        meal_type=row[IDX_MEAL_TYPE].strip() if row[IDX_MEAL_TYPE] else None,
                        # Kolom lain yang tidak ada di CSV ini akan default ke None/nilai default model
                        # seperti pufa, cholesterol, vitamin_a, vitamin_e, dll.
                        # origin dan image_url juga akan None kecuali diisi cara lain
                    )
                    db.session.add(food)
                    count += 1

                    if count % 200 == 0: # Commit setiap 200 baris untuk efisiensi
                        db.session.commit()
                        click.echo(f"Processed and committed {count} foods...")

                except IndexError:
                    click.echo(f"Error processing row {row_number}: {row}. IndexError. Ensure CSV format is correct and has {EXPECTED_COLUMNS} columns.")
                except ValueError as e:
                    click.echo(f"Error processing row {row_number}: {row}. ValueError: {str(e)}. Check data types.")
                except Exception as e:
                    click.echo(f"An unexpected error occurred at row {row_number}: {row}. Error: {str(e)}")
                    db.session.rollback() # Rollback jika ada error di tengah batch

        db.session.commit() # Commit sisa data
        click.echo(f"Successfully imported {count} food items from {file_path}.")

        if classify and count > 0: 
            click.echo("Classifying foods for dietary preferences and allergens...")
            try:
                classifier = FoodClassifier() # Pastikan FoodClassifier kompatibel dengan model baru
                classifier.classify_foods()
                click.echo("Food classification complete.")
            except Exception as e:
                click.echo(f"Error during food classification: {str(e)}")
        elif not classify:
            click.echo("Skipping food classification as per --classify=False.")
        elif count == 0:
            click.echo("No food data imported, skipping classification.")

    except FileNotFoundError:
        click.echo(f"Error: File not found at {file_path}. Please ensure the dataset exists at this location relative to the backend directory.")
        click.echo("Current working directory might affect relative paths. Try providing an absolute path if issues persist.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"An unexpected error occurred during import: {str(e)}")


@click.command('classify-foods')
@with_appcontext
def classify_foods_command():
    """Classify foods based on dietary preferences and allergies"""
    try:
        classifier = FoodClassifier()
        classifier.classify_foods()
        click.echo(
            'Successfully classified foods for vegetarian, halal, and allergen content')
    except Exception as e:
        click.echo(f'Error classifying foods: {str(e)}')
        
def calculate_bmi(weight, height_cm):
    """Menghitung BMI dari berat (kg) dan tinggi (cm)."""
    if not weight or not height_cm or height_cm == 0:
        return None
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)

def get_nutrition_score_for_single_food(nutrition_recommender, user, goal, food_item):
    """
    Menghitung skor nutrisi untuk satu item makanan spesifik berdasarkan profil pengguna dan tujuan.
    Versi ini telah disesuaikan untuk mendapatkan distribusi skor yang lebih baik.
    """
    nutritional_needs = nutrition_recommender._calculate_nutritional_needs(user, goal)
    medical_condition = nutritional_needs['medical_condition']

    # Penalti Awal jika tidak cocok secara medis
    if not nutrition_recommender._is_suitable_for_medical_condition(food_item, medical_condition):
        return 0.01 # Skor sangat rendah, tapi tidak nol absolut agar terlihat di distribusi

    # Target nutrisi per makanan
    num_main_meals = nutritional_needs.get('num_main_meals', 4 if medical_condition == 'obesity' else 3)

    # Pastikan num_main_meals tidak nol untuk menghindari ZeroDivisionError
    if num_main_meals == 0: num_main_meals = 3 # Default fallback

    calories_per_meal = nutritional_needs['daily_calories'] / num_main_meals
    protein_per_meal = nutritional_needs['protein_g_per_day'] / num_main_meals
    carbs_per_meal = nutritional_needs['carbs_g_per_day'] / num_main_meals
    fat_per_meal = nutritional_needs['fat_g_per_day'] / num_main_meals
    
    # Batas-batas dengan sedikit kelonggaran
    # Ambil dari nutritional_needs jika ada, jika tidak, hitung dengan kelonggaran
    max_calories_per_meal = nutritional_needs.get('max_calories_per_meal', calories_per_meal * 1.5) 
    # Untuk diabetes, batas karbohidrat lebih ketat, tapi beri sedikit ruang dari target per meal
    base_carbs_target_diabetes = carbs_per_meal * 0.5 # Misal target 50% dari karbohidrat normal per meal untuk diabetes
    max_carbs_per_meal_strict = nutritional_needs.get('max_carbs_per_meal_diabetes', base_carbs_target_diabetes) if medical_condition == 'diabetes' else carbs_per_meal * 1.5
    max_sodium_per_meal = nutritional_needs.get('target_sodium_mg_per_meal', 700) # Asumsi batas sodium per meal

    # Penalti jika MELEBIHI batas tertentu, tapi tidak langsung 0
    penalty_score = 1.0
    if food_item.caloric_value is not None and food_item.caloric_value > max_calories_per_meal * 1.1: # Penalti jika > 10% di atas max
        penalty_score *= 0.7
    if medical_condition == 'diabetes' and food_item.carbohydrates is not None and food_item.carbohydrates > max_carbs_per_meal_strict * 1.1: # Penalti jika >10% di atas max untuk diabetes
        penalty_score *= 0.6
    if medical_condition == 'hypertension' and food_item.sodium is not None and food_item.sodium > max_sodium_per_meal * 1.1: # Penalti jika >10% di atas max untuk hipertensi
        penalty_score *= 0.7

    # Perhitungan skor komponen (menggunakan rasio kuadrat untuk deviasi)
    calorie_score = 0
    if food_item.caloric_value is not None and calories_per_meal > 0:
        calorie_diff_ratio = abs(food_item.caloric_value - calories_per_meal) / calories_per_meal
        calorie_score = max(0, 1 - calorie_diff_ratio**2) 
        if medical_condition == 'obesity':
            if food_item.caloric_value < calories_per_meal * 0.8: calorie_score = min(1, calorie_score * 1.15) # Bonus jika rendah kalori
            elif food_item.caloric_value > calories_per_meal * 1.05: calorie_score *= 0.8 # Penalti jika sedikit di atas

    protein_score = 0
    if food_item.protein is not None and protein_per_meal > 0:
        protein_diff_ratio = abs(food_item.protein - protein_per_meal) / protein_per_meal
        protein_score = max(0, 1 - protein_diff_ratio**2)
        if medical_condition == 'obesity' and food_item.protein > protein_per_meal * 0.9: protein_score = min(1, protein_score * 1.1)

    carb_score = 0
    if food_item.carbohydrates is not None and carbs_per_meal > 0:
        carb_target_for_scoring = max_carbs_per_meal_strict if medical_condition == 'diabetes' else carbs_per_meal
        if carb_target_for_scoring > 0:
            carb_diff_ratio = abs(food_item.carbohydrates - carb_target_for_scoring) / carb_target_for_scoring
            carb_score = max(0, 1 - carb_diff_ratio**2)
            if medical_condition == 'diabetes' and food_item.carbohydrates > carb_target_for_scoring: carb_score *= 0.7
        else: # Jika target karbohidrat sangat rendah (misalnya 0 untuk diet tertentu)
            carb_score = 1 if (food_item.carbohydrates is None or food_item.carbohydrates <= 1) else 0 # Skor tinggi jika karbohidrat sangat rendah


    fat_score = 0
    if food_item.fat is not None and fat_per_meal > 0:
        fat_diff_ratio = abs(food_item.fat - fat_per_meal) / fat_per_meal
        fat_score = max(0, 1 - fat_diff_ratio**2)
        if medical_condition in ['hypertension', 'obesity'] and food_item.fat > fat_per_meal * 1.05: fat_score *= 0.8

    micronutrient_score_adj = nutrition_recommender._calculate_micronutrient_score(food_item, nutritional_needs)
    
    # Ambil bobot dari instance nutrition_recommender
    weights = {
        'calorie': getattr(nutrition_recommender, 'calorie_match_weight', 0.3), # Default jika atribut tidak ada
        'protein': getattr(nutrition_recommender, 'protein_match_weight', 0.25),
        'carb': getattr(nutrition_recommender, 'carb_match_weight', 0.2),
        'fat': getattr(nutrition_recommender, 'fat_match_weight', 0.15),
        'micro': getattr(nutrition_recommender, 'micronutrient_adjustment_weight', 0.1)
    }
    
    # Normalisasi bobot agar totalnya 1 (jika tidak, bisa menghasilkan skor di luar 0-1)
    total_weight = sum(weights.values())
    if total_weight > 0:
        for key in weights:
            weights[key] /= total_weight
    else: # Jika semua bobot 0, set bobot kalori ke 1 sebagai fallback
        weights['calorie'] = 1.0


    weighted_score = (
        calorie_score * weights['calorie'] +
        protein_score * weights['protein'] +
        carb_score * weights['carb'] +
        fat_score * weights['fat'] +
        micronutrient_score_adj * weights['micro']
    )
    
    final_score = weighted_score * penalty_score # Terapkan penalti di akhir
    return max(0, min(1, final_score)) # Pastikan skor antara 0 dan 1


@click.command('generate-dt-dataset')
@click.option('--output-file', default='decision_tree_training_data.csv', help='Nama file CSV output.')
@click.option('--threshold', default=0.5, type=float, help='Ambang batas skor nutrisi untuk label biner (akan ditentukan setelah melihat distribusi).')
@click.option('--user-sample-size', default=None, type=int, help='Jumlah sampel pengguna (opsional, ambil semua jika None).')
@click.option('--food-sample-size', default=None, type=int, help='Jumlah sampel makanan per pengguna (opsional, ambil semua jika None).')
@with_appcontext
def generate_dt_dataset_command(output_file, threshold, user_sample_size, food_sample_size):
    """Membuat dataset CSV untuk melatih Decision Tree dan menampilkan statistik skor mentah."""
    click.echo(f"Memulai pembuatan dataset. Threshold awal (mungkin diabaikan): {threshold}")
    click.echo("Fokus utama adalah mendapatkan statistik skor mentah terlebih dahulu.")

    nutrition_recommender = NutritionDecisionTree()

    users_with_goals_query = User.query.join(DietGoal).filter(DietGoal.status == 'active')
    if user_sample_size:
        users_with_goals_query = users_with_goals_query.limit(user_sample_size)
    users_with_goals = users_with_goals_query.all()

    if not users_with_goals:
        click.echo("Tidak ada pengguna dengan tujuan diet aktif ditemukan.")
        return

    all_foods = Food.query.all()
    if not all_foods:
        click.echo("Tidak ada data makanan ditemukan.")
        return

    click.echo(f"Ditemukan {len(users_with_goals)} pengguna dengan tujuan aktif dan {len(all_foods)} makanan.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir_for_output = os.path.abspath(os.path.join(script_dir, '..', 'dataset-diet'))
    os.makedirs(base_dir_for_output, exist_ok=True)
    csv_file_path = os.path.join(base_dir_for_output, output_file)

    user_feature_names = [
        'user_age', 'user_weight', 'user_height', 'user_bmi',
        'user_gender_F', 'user_gender_M',
        'user_activity_level_sedentary', 'user_activity_level_light', 
        'user_activity_level_moderate', 'user_activity_level_active', 'user_activity_level_very_active',
        'user_medical_condition_none', 'user_medical_condition_diabetes', 
        'user_medical_condition_hypertension', 'user_medical_condition_obesity',
        'user_target_weight',
        'user_daily_calories_need', 'user_protein_need_g', 'user_carbs_need_g', 'user_fat_need_g'
    ]
    food_feature_names = [
        'food_caloric_value', 'food_protein_g', 'food_lemak_g', 'food_karbohidrat_g', 'food_serat_g',
        'food_kalsium_mg', 'food_fosfor_mg', 'food_besi_mg', 'food_natrium_mg', 'food_kalium_mg',
        'food_tembaga_mg', 'food_seng_mg', 'food_retinol_mcg', 'food_thiamin_mg',
        'food_riboflavin_mg', 'food_niasin_mg', 'food_vitamin_c_mg',
        'food_status_makanan_Olahan', 'food_status_makanan_Tunggal', 'food_status_makanan_Bahan_Dasar', # underscore
        'food_kelompok_makanan_Buah', 'food_kelompok_makanan_Sayur', 'food_kelompok_makanan_Kacang',
        'food_kelompok_makanan_Serealia', 'food_kelompok_makanan_Umbi', 'food_kelompok_makanan_Daging',
        'food_kelompok_makanan_Ikan_dsb', 'food_kelompok_makanan_Susu', 'food_kelompok_makanan_Telur', # underscore
        'food_is_vegetarian', 'food_is_halal', 'food_contains_dairy', 'food_contains_nuts',
        'food_contains_seafood', 'food_contains_eggs', 'food_contains_soy'
    ]
    
    possible_genders = ['M', 'F']
    possible_activity_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
    possible_medical_conditions = ['none', 'diabetes', 'hypertension', 'obesity']
    # PASTIKAN NILAI INI SESUAI DENGAN DATA ANDA
    possible_food_statuses = ['Olahan', 'Tunggal', 'Bahan Dasar'] 
    possible_food_groups = [ 
        'Buah', 'Sayur', 'Kacang', 'Serealia', 'Umbi', 
        'Daging', 'Ikan dsb', 'Susu', 'Telur' 
    ]

    header = user_feature_names + food_feature_names + ['raw_nutrition_score', 'label_recommended'] # Tambah raw_nutrition_score
    
    dataset_rows = []
    all_raw_scores = [] # Untuk menyimpan semua skor mentah
    processed_count = 0

    for user in users_with_goals:
        active_goal = DietGoal.query.filter_by(user_id=user.id, status='active').order_by(DietGoal.created_at.desc()).first()
        if not active_goal:
            continue

        nutritional_needs = nutrition_recommender._calculate_nutritional_needs(user, active_goal)
        user_features = {
            'user_age': user.age, 'user_weight': user.weight, 'user_height': user.height,
            'user_bmi': calculate_bmi(user.weight, user.height),
            'user_target_weight': active_goal.target_weight,
            'user_daily_calories_need': nutritional_needs['daily_calories'],
            'user_protein_need_g': nutritional_needs['protein_g_per_day'],
            'user_carbs_need_g': nutritional_needs['carbs_g_per_day'],
            'user_fat_need_g': nutritional_needs['fat_g_per_day']
        }
        for gender_val in possible_genders: user_features[f'user_gender_{gender_val}'] = 1 if user.gender == gender_val else 0
        for level_val in possible_activity_levels: user_features[f'user_activity_level_{level_val.replace(" ", "_")}'] = 1 if user.activity_level == level_val else 0
        for med_val in possible_medical_conditions: user_features[f'user_medical_condition_{med_val}'] = 1 if active_goal.medical_condition == med_val else 0
        
        current_foods_to_process = all_foods
        if food_sample_size and len(all_foods) > food_sample_size:
            current_foods_to_process = random.sample(all_foods, food_sample_size)

        for food in current_foods_to_process:
            nutrition_score = get_nutrition_score_for_single_food(nutrition_recommender, user, active_goal, food)
            all_raw_scores.append(nutrition_score) # Simpan skor mentah

            # Label akan ditentukan nanti setelah melihat distribusi skor
            # Untuk sementara, kita bisa set default atau menggunakan threshold awal
            label = 1 if nutrition_score >= threshold else 0 # Threshold ini akan kita sesuaikan

            food_features = {
                'food_caloric_value': food.caloric_value, 'food_protein_g': food.protein,
                'food_lemak_g': food.fat, 'food_karbohidrat_g': food.carbohydrates,
                'food_serat_g': food.dietary_fiber, 'food_kalsium_mg': food.calcium,
                'food_fosfor_mg': food.phosphorus, 'food_besi_mg': food.iron,
                'food_natrium_mg': food.sodium, 'food_kalium_mg': food.potassium,
                'food_tembaga_mg': food.copper, 'food_seng_mg': food.zinc,
                'food_retinol_mcg': food.retinol_mcg, 'food_thiamin_mg': food.thiamin_mg,
                'food_riboflavin_mg': food.riboflavin_mg, 'food_niasin_mg': food.niacin_mg,
                'food_vitamin_c_mg': food.vitamin_c,
                'food_is_vegetarian': 1 if food.is_vegetarian else 0,
                'food_is_halal': 1 if food.is_halal else 0,
                'food_contains_dairy': 1 if food.contains_dairy else 0,
                'food_contains_nuts': 1 if food.contains_nuts else 0,
                'food_contains_seafood': 1 if food.contains_seafood else 0,
                'food_contains_eggs': 1 if food.contains_eggs else 0,
                'food_contains_soy': 1 if food.contains_soy else 0
            }
            for status_val in possible_food_statuses: food_features[f'food_status_makanan_{status_val.replace(" ", "_")}'] = 1 if food.food_status == status_val else 0
            for group_val in possible_food_groups: food_features[f'food_kelompok_makanan_{group_val.replace(" ", "_").replace("dsb", "dll")}'] = 1 if food.food_group == group_val else 0
            
            row_data = []
            for feature_name in user_feature_names: row_data.append(user_features.get(feature_name, 0 if 'user_gender' in feature_name or 'user_activity_level' in feature_name or 'user_medical_condition' in feature_name else None))
            for feature_name in food_feature_names:
                default_val_food = 0 if 'food_status_makanan' in feature_name or 'food_kelompok_makanan' in feature_name or feature_name.startswith('food_is_') or feature_name.startswith('food_contains_') else None
                row_data.append(food_features.get(feature_name, default_val_food))
            
            row_data.append(nutrition_score) # Tambahkan skor mentah ke baris CSV
            row_data.append(label)
            dataset_rows.append(row_data)
            
            processed_count += 1
            if processed_count % 1000 == 0: # Kurangi frekuensi print
                click.echo(f"Memproses pasangan pengguna-makanan ke-{processed_count}...")

    # Tampilkan statistik skor mentah
    if all_raw_scores:
        click.echo(f"\n--- Statistik Skor Mentah (Total {len(all_raw_scores)} skor) ---")
        click.echo(f"Min Skor: {np.min(all_raw_scores):.4f}")
        click.echo(f"Max Skor: {np.max(all_raw_scores):.4f}")
        click.echo(f"Mean Skor: {np.mean(all_raw_scores):.4f}")
        click.echo(f"Median Skor: {np.median(all_raw_scores):.4f}")
        click.echo(f"25th Percentile: {np.percentile(all_raw_scores, 25):.4f}")
        click.echo(f"50th Percentile (Median): {np.percentile(all_raw_scores, 50):.4f}")
        click.echo(f"75th Percentile: {np.percentile(all_raw_scores, 75):.4f}")
        click.echo(f"90th Percentile: {np.percentile(all_raw_scores, 90):.4f}")
        click.echo(f"95th Percentile: {np.percentile(all_raw_scores, 95):.4f}")
        click.echo(f"Jumlah skor > 0.5: {sum(s > 0.5 for s in all_raw_scores)}")
        click.echo(f"Jumlah skor > 0.6: {sum(s > 0.6 for s in all_raw_scores)}")
        click.echo(f"Jumlah skor > 0.7: {sum(s > 0.7 for s in all_raw_scores)}")
        click.echo("----------------------------------------------------")
        click.echo("\nSARAN: Gunakan statistik di atas untuk menentukan --threshold yang lebih baik saat menjalankan ulang perintah ini untuk membuat CSV final.")
    else:
        click.echo("Tidak ada skor mentah yang dihasilkan.")

    # Tulis ke file CSV (masih menggunakan threshold awal, atau threshold yang Anda tentukan)
    # Anda mungkin ingin menjalankan ulang perintah ini dengan threshold yang disesuaikan setelah melihat statistik
    try:
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            # Jika Anda ingin memperbarui label berdasarkan threshold baru di sini, Anda perlu loop lagi
            # atau simpan dataset_rows dengan skor mentah dan hitung ulang label sebelum menulis.
            # Untuk sekarang, kita tulis dengan label berdasarkan threshold awal.
            # Untuk pembuatan CSV final, Anda akan menjalankan ulang perintah dengan threshold yang lebih baik.
            updated_dataset_rows = []
            if all_raw_scores and dataset_rows: # Pastikan ada data
                # Jika Anda ingin langsung menggunakan threshold baru dari statistik (misal median)
                # new_threshold_from_stats = np.median(all_raw_scores)
                # click.echo(f"Menggunakan threshold baru dari median skor: {new_threshold_from_stats:.4f} untuk CSV.")
                # for i, row in enumerate(dataset_rows):
                #     raw_score_idx = header.index('raw_nutrition_score')
                #     label_idx = header.index('label_recommended')
                #     row[label_idx] = 1 if row[raw_score_idx] >= new_threshold_from_stats else 0
                #     updated_dataset_rows.append(row)
                # writer.writerows(updated_dataset_rows)
                writer.writerows(dataset_rows) # Untuk saat ini, tulis dengan threshold awal
            else:
                 writer.writerows(dataset_rows)


        click.echo(f"\nDataset (mungkin dengan label sementara) berhasil dibuat dan disimpan di: {csv_file_path}")
        click.echo(f"Total {len(dataset_rows)} baris data dihasilkan.")
        click.echo(f"PERHATIAN: Label di CSV ini mungkin perlu diperbarui dengan menjalankan ulang perintah menggunakan --threshold yang lebih sesuai berdasarkan statistik skor mentah di atas.")

    except IOError as e:
        click.echo(f"Gagal menulis ke file CSV: {e}")
    except Exception as e:
        click.echo(f"Terjadi kesalahan saat menulis CSV: {e}")


def register_commands(app):
    app.cli.add_command(seed_users_command)
    app.cli.add_command(import_nutrition_data_command) # Nama perintah diperbarui
    app.cli.add_command(classify_foods_command)
    app.cli.add_command(generate_dt_dataset_command)

