import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User
from app.models.recommendation import DietGoal
from datetime import datetime, timedelta
import random
from sqlalchemy import func
import csv
from app.models.food import Food
from app.utils.food_classifier import FoodClassifier
from app.models.recommendation import Recommendation


@click.command('seed-users')
@click.option('--count', default=10, help='Number of users to create')
@with_appcontext
def seed_users_command(count):
    """Seed database with sample users"""
    try:
        # Get the highest existing user ID
        max_user_id = db.session.query(func.max(User.id)).scalar() or 0

        # Create test users
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
            db.session.flush()  # Get the ID before committing

            # Create diet goal using the actual user ID - only weight_loss now
            goal = DietGoal(
                user_id=user.id,  # Use the actual user ID
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


KJ_TO_KCAL = 1 / 4.184
@click.command('import-indonesian-foods')
@click.option('--source', default='dataset-diet', help='Source directory for data files. Default: dataset-diet')
@click.option('--filename', default='foods_updated.csv', help='Filename of the CSV data. Default: foods_updated.csv') # Default diubah
@click.option('--classify', default=True, type=bool, help='Run food classifier after import. Default: True')
@with_appcontext
def import_indonesian_foods(source, filename, classify):
    """Import Indonesian foods from the foods_updated.csv dataset."""
    try:
        # Hapus semua data rekomendasi yang terkait dengan makanan yang ada
        num_deleted_recs = Recommendation.query.delete()
        db.session.commit()
        click.echo(f"Deleted {num_deleted_recs} existing recommendation records.")

        # Hapus semua data makanan yang ada untuk menghindari duplikasi
        num_deleted_foods = Food.query.delete()
        db.session.commit()
        click.echo(f"Deleted {num_deleted_foods} existing food records.")

        file_path = f'./{source}/{filename}'
        count = 0
        
        # Indeks kolom berdasarkan file foods_updated.csv
        # Kolom: id,Menu,Energy (kJ),Protein (g),Fat (g),Carbohydrates (g),Dietary Fiber (g),
        # PUFA (g),Cholesterol (mg),Vitamin A (mg),Vitamin E (eq.) (mg),Vitamin B1 (mg),
        # Vitamin B2 (mg),Vitamin B6 (mg),Total Folic Acid (µg),Vitamin C (mg),Sodium (mg),
        # Potassium (mg),Calcium (mg),Magnesium (mg),Phosphorus (mg),Iron (mg),Zinc (mg),meal_type
        
        IDX_ID_CSV = 0 # Kolom 'id' dari CSV (bukan primary key tabel)
        IDX_NAME = 1
        IDX_ENERGY_KJ = 2
        IDX_PROTEIN = 3
        IDX_FAT = 4
        IDX_CARBOHYDRATES = 5
        IDX_DIETARY_FIBER = 6
        IDX_PUFA = 7
        IDX_CHOLESTEROL = 8
        IDX_VITAMIN_A = 9
        IDX_VITAMIN_E = 10
        IDX_VITAMIN_B1 = 11
        IDX_VITAMIN_B2 = 12
        IDX_VITAMIN_B6 = 13
        IDX_TOTAL_FOLIC_ACID = 14
        IDX_VITAMIN_C = 15
        IDX_SODIUM = 16
        IDX_POTASSIUM = 17
        IDX_CALCIUM = 18
        IDX_MAGNESIUM = 19
        IDX_PHOSPHORUS = 20
        IDX_IRON = 21
        IDX_ZINC = 22
        IDX_MEAL_TYPE_CSV = 23 # Kolom 'meal_type' dari CSV, tidak disimpan langsung ke model Food

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader) 
            click.echo(f"CSV Header: {header}")
            if len(header) < IDX_MEAL_TYPE_CSV + 1:
                click.echo(f"Error: CSV file '{filename}' does not have the expected number of columns (at least {IDX_MEAL_TYPE_CSV + 1}). Found {len(header)} columns.")
                return

            for row_number, row in enumerate(reader, 1):
                try:
                    if not any(field.strip() for field in row):
                        continue

                    if len(row) < IDX_MEAL_TYPE_CSV + 1:
                        click.echo(f"Skipping row {row_number} due to insufficient columns: {row}")
                        continue

                    name = row[IDX_NAME].strip()
                    if not name:
                        click.echo(f"Skipping row {row_number} due to empty food name.")
                        continue
                        
                    def safe_float_conversion(value_str, default=0.0):
                        try:
                            # Mengganti koma dengan titik untuk desimal jika ada
                            cleaned_value_str = str(value_str).replace(',', '.').strip()
                            return float(cleaned_value_str) if cleaned_value_str else default
                        except ValueError:
                            # click.echo(f"Warning: Could not convert '{value_str}' to float for food '{name}'. Using default {default}.")
                            return default

                    energy_kj = safe_float_conversion(row[IDX_ENERGY_KJ])
                    caloric_value_kcal = energy_kj * KJ_TO_KCAL
                    
                    # Kolom meal_type dari CSV tidak disimpan ke model Food,
                    # karena meal_type pada rekomendasi akan diprediksi oleh ML.
                    # Data meal_type dari CSV ini akan digunakan untuk melatih model ML.

                    food = Food(
                        name=name,
                        energy_kj=energy_kj,
                        caloric_value=caloric_value_kcal,
                        protein=safe_float_conversion(row[IDX_PROTEIN]),
                        fat=safe_float_conversion(row[IDX_FAT]),
                        carbohydrates=safe_float_conversion(row[IDX_CARBOHYDRATES]),
                        dietary_fiber=safe_float_conversion(row[IDX_DIETARY_FIBER]),
                        pufa=safe_float_conversion(row[IDX_PUFA]),
                        cholesterol=safe_float_conversion(row[IDX_CHOLESTEROL]),
                        vitamin_a=safe_float_conversion(row[IDX_VITAMIN_A]),
                        vitamin_e=safe_float_conversion(row[IDX_VITAMIN_E]),
                        vitamin_b1=safe_float_conversion(row[IDX_VITAMIN_B1]),
                        vitamin_b2=safe_float_conversion(row[IDX_VITAMIN_B2]),
                        vitamin_b6=safe_float_conversion(row[IDX_VITAMIN_B6]),
                        total_folic_acid=safe_float_conversion(row[IDX_TOTAL_FOLIC_ACID]),
                        vitamin_c=safe_float_conversion(row[IDX_VITAMIN_C]),
                        sodium=safe_float_conversion(row[IDX_SODIUM]),
                        potassium=safe_float_conversion(row[IDX_POTASSIUM]),
                        calcium=safe_float_conversion(row[IDX_CALCIUM]),
                        magnesium=safe_float_conversion(row[IDX_MAGNESIUM]),
                        phosphorus=safe_float_conversion(row[IDX_PHOSPHORUS]),
                        iron=safe_float_conversion(row[IDX_IRON]),
                        zinc=safe_float_conversion(row[IDX_ZINC]),
                    )
                    db.session.add(food)
                    count += 1

                    if count % 200 == 0:
                        db.session.commit()
                        click.echo(f"Processed and committed {count} foods...")

                except IndexError as e:
                    click.echo(f"Error processing row {row_number}: {row}. IndexError: {str(e)}. Ensure CSV format is correct.")
                except ValueError as e:
                    click.echo(f"Error processing row {row_number}: {row}. ValueError: {str(e)}. Check data types.")
                except Exception as e:
                    click.echo(f"An unexpected error occurred at row {row_number}: {row}. Error: {str(e)}")
                    db.session.rollback() 

        db.session.commit() 
        click.echo(f"Successfully imported {count} Indonesian foods from {file_path}.")

        if classify and count > 0: 
            click.echo("Classifying foods for dietary preferences and allergens...")
            classifier = FoodClassifier()
            classifier.classify_foods()
            click.echo("Food classification complete.")
        elif not classify:
            click.echo("Skipping food classification as per --classify=False.")
        elif count == 0:
            click.echo("No food data imported, skipping classification.")

    except FileNotFoundError:
        click.echo(f"Error: File not found at {file_path}. Please ensure the dataset exists in '{source}/{filename}'.")
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

    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


def register_commands(app):
    app.cli.add_command(seed_users_command)
    app.cli.add_command(import_indonesian_foods)
    app.cli.add_command(classify_foods_command)
