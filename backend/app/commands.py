import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User
from app.models.recommendation import DietGoal
from datetime import datetime, timedelta
import random
from sqlalchemy import func
import pandas as pd
import csv
from app.models.food import Food
from app.utils.food_classifier import FoodClassifier


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


@click.command('import-indonesian-foods')
@click.option('--source', default='dataset-diet', help='Source directory for data files (dataset or dataset-diet)')
@click.option('--classify', default=True, help='Run food classifier after import')
@with_appcontext
def import_indonesian_foods(source, classify):
    """Import Indonesian foods with only macronutrient data"""
    try:
        # First, delete all existing foods to avoid duplicates or conflicts
        num_deleted = Food.query.delete()
        db.session.commit()
        click.echo(f"Deleted {num_deleted} existing food records")

        # Determine file path based on source option
        file_path = f'../{source}/nutrition.csv'
        count = 0

        # Open and process the CSV file
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row

            for row in reader:
                try:
                    if len(row) >= 6:  # Ensure row has enough columns
                        # CSV format: id, calories, protein, fat, carbs, name, image_url
                        calories = float(row[1]) if row[1] else 0
                        protein = float(row[2]) if row[2] else 0
                        fat = float(row[3]) if row[3] else 0
                        carbs = float(row[4]) if row[4] else 0
                        name = row[5]
                        image_url = row[6] if len(row) > 6 and row[6] else None

                        # Create a new food entry
                        food = Food(
                            name=name,
                            caloric_value=calories,
                            protein=protein,
                            carbohydrates=carbs,
                            fat=fat,
                            image_url=image_url,
                            # Default values for allergens
                            contains_dairy=False,
                            contains_nuts=False,
                            contains_seafood=False,
                            contains_eggs=False,
                            contains_soy=False,
                            # Default dietary values
                            is_vegetarian=False,
                            is_halal=True
                        )
                        db.session.add(food)
                        count += 1

                        if count % 100 == 0:
                            db.session.commit()
                            click.echo(f"Processed {count} foods")

                except (ValueError, IndexError) as e:
                    click.echo(f"Error processing row: {row}. Error: {str(e)}")

        db.session.commit()
        click.echo(f"Successfully imported {count} Indonesian foods")

        # Run classifier to set dietary categories and allergens if requested
        if classify:
            click.echo(
                "Classifying foods for dietary preferences and allergens...")
            classifier = FoodClassifier()
            classifier.classify_foods()

    except Exception as e:
        db.session.rollback()
        click.echo(f"Error: {str(e)}")


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
