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


def register_commands(app):
    app.cli.add_command(seed_users_command)
    app.cli.add_command(import_nutrition_data_command) # Nama perintah diperbarui
    app.cli.add_command(classify_foods_command)

