"""Complete schema rebuild for Indonesian diet system

Revision ID: 759e3c8dd00d
Revises: 2c12414bc3b9
Create Date: 2025-04-30 16:22:51.152996

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '759e3c8dd00d'
down_revision = '2c12414bc3b9'
branch_labels = None
depends_on = None


def upgrade():
    # Disable foreign key checks to allow dropping tables with dependencies
    op.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    # Drop all existing tables
    tables = [
        'recommendations', 
        'food_preferences', 
        'diet_goals', 
        'foods', 
        'weight_progress',
        # Add any other tables that might exist in your schema
    ]
    
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS {table};")
    
    # Re-enable foreign key checks
    op.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    # Create foods table with simplified schema focused on Indonesian foods
    op.create_table(
        'foods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('caloric_value', sa.Float(), nullable=True),
        sa.Column('protein', sa.Float(), nullable=True),
        sa.Column('carbohydrates', sa.Float(), nullable=True),
        sa.Column('fat', sa.Float(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        # Dietary Categories
        sa.Column('is_vegetarian', sa.Boolean(), default=False, nullable=True),
        sa.Column('is_halal', sa.Boolean(), default=True, nullable=True),
        # Allergen Information
        sa.Column('contains_dairy', sa.Boolean(), default=False, nullable=True),
        sa.Column('contains_nuts', sa.Boolean(), default=False, nullable=True),
        sa.Column('contains_seafood', sa.Boolean(), default=False, nullable=True),
        sa.Column('contains_eggs', sa.Boolean(), default=False, nullable=True),
        sa.Column('contains_soy', sa.Boolean(), default=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create diet_goals table focused on weight loss only
    op.create_table(
        'diet_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_weight', sa.Float(), nullable=False),
        sa.Column('target_date', sa.Date(), nullable=False),
        sa.Column('medical_condition', sa.Enum('none', 'diabetes', 'hypertension', 'obesity'), 
                  server_default='none', nullable=False),
        sa.Column('status', sa.Enum('active', 'completed', 'abandoned'), 
                  server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create food_preferences table with limited preference types
    op.create_table(
        'food_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preference_type', sa.Enum(
            'vegetarian', 'halal', 
            'dairy_free', 'nut_free', 'seafood_free', 'egg_free', 'soy_free'
        ), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('food_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('recommendation_date', sa.Date(), nullable=False),
        sa.Column('is_consumed', sa.Boolean(), default=False, nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('feedback_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.ForeignKeyConstraint(['food_id'], ['foods.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create weight_progress table for tracking progress
    op.create_table(
        'weight_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Since this is a complete rebuild, downgrade would just drop all tables
    # No specific downgrade implementation needed as it's a starting point
    pass
