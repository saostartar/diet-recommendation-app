from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.food import Food
from app.models.recommendation import Recommendation, DietGoal, FoodPreference
from app.utils.collaborative_filtering import DietCollaborativeFiltering
from app.utils.decision_tree import NutritionDecisionTree
from app.utils.hybrid_recommender import HybridDietRecommender
from app import db
from datetime import datetime, date
import re

bp = Blueprint('recommendation', __name__)

# Helper function to validate image URLs - same as in food.py
def validate_image_url(url):
    if not url or not isinstance(url, str):
        return "https://via.placeholder.com/300x200.png?text=Tidak+ada+gambar"
    
    # Clean the URL string - remove any unexpected characters
    url = url.strip()
    
    # Check if it's already a valid URL format (starts with http/https or /)
    if url.startswith(('http://', 'https://', '/')):
        return url
    
    # Try to extract any valid URL from text like "image.jpg (600×450) (example.com)"
    url_match = re.search(r'https?://[^\s)]+', url)
    if url_match:
        return url_match.group(0)
    
    # For cases like "kripik_tempe_abadi.jpg (600x450) (bukalapak.com)"
    # Extract the filename and convert to a relative path
    filename_match = re.search(r'^([^(\s]+)', url)
    if filename_match:
        filename = filename_match.group(1).strip()
        # Return a path to static images - ensure this is always a valid path structure
        return f"/static/food_images/{filename}"
    
    # Default placeholder
    return "https://via.placeholder.com/300x200.png?text=Tidak+ada+gambar"


@bp.route('/preferences', methods=['GET', 'POST'])
@jwt_required()
def set_preferences():
    """Handle food preferences"""
    try:
        user_id = get_jwt_identity()

        if request.method == 'GET':
            preferences = FoodPreference.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            # Group into dietary preferences and allergies
            dietary_prefs = []
            allergies = []
            
            for pref in preferences:
                if pref.preference_type in ['vegetarian', 'halal']:
                    dietary_prefs.append(pref.preference_type)
                else:
                    allergies.append(pref.preference_type)

            return jsonify({
                'has_preferences': bool(preferences),
                'preferences': {
                    'diet_type': dietary_prefs[0] if dietary_prefs else '',
                    'allergies': allergies
                } if preferences else {}
            }), 200

        # POST request
        data = request.get_json()

        # Deactivate existing preferences
        FoodPreference.query.filter_by(
            user_id=user_id).update({'is_active': False})

        # Create new preferences
        preferences = []

        # Add diet type preference
        if data.get('diet_type'):
            preferences.append(FoodPreference(
                user_id=user_id,
                preference_type=data['diet_type'],
                is_active=True
            ))

        # Add allergy preferences
        for allergy in data.get('allergies', []):
            preferences.append(FoodPreference(
                user_id=user_id,
                preference_type=allergy,
                is_active=True
            ))

        db.session.add_all(preferences)
        db.session.commit()

        return jsonify({'message': 'Preferensi makanan berhasil disimpan'}), 201

    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500


@bp.route('/diet-goals', methods=['POST'])
@jwt_required()
def create_diet_goal():
    """Set weight loss goal with medical condition"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Deactivate existing goals
        DietGoal.query.filter_by(
            user_id=user_id,
            status='active'
        ).update({'status': 'abandoned'})

        # Create new goal
        new_goal = DietGoal(
            user_id=user_id,
            target_weight=float(data['target_weight']),
            target_date=datetime.strptime(
                data['target_date'], '%Y-%m-%d').date(),
            medical_condition=data.get('medical_condition', 'none'),
            status='active'
        )

        db.session.add(new_goal)
        db.session.commit()

        return jsonify({'message': 'Tujuan diet berhasil disimpan'}), 201
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500





@bp.route('/recommend/daily-menu', methods=['GET'])
@jwt_required()
def get_daily_menu():
    """Generate personalized daily menu based on ML-classified meal types"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Get active preferences
        preferences = FoodPreference.query.filter_by(
            user_id=user_id,
            is_active=True
        ).all()
        
        preference_types = [p.preference_type for p in preferences]
        print(f"Active preferences: {preference_types}")

        # Get active goal
        goal = DietGoal.query.filter_by(
            user_id=user_id,
            status='active'
        ).first_or_404()

        # Get recommendations with ML-classified meal types
        # Increase recommendations to get more variety
        recommender = HybridDietRecommender()
        recommendations = recommender.get_recommendations(
            user=user,
            goal=goal,
            n_recommendations=500,  # Increased to get more variety
            preferences=preference_types
        )
        
        print(f"Got {len(recommendations)} initial recommendations")

        # Create recommendations in database
        current_date = datetime.now().date()
        
        # First remove any existing recommendations for today
        Recommendation.query.filter_by(
            user_id=user_id,
            recommendation_date=current_date
        ).delete()
        db.session.commit()

        # Group recommendations by meal type
        meal_type_recommendations = {
            'Sarapan': [],
            'Makan Siang': [],
            'Makan Malam': [],
            'Cemilan': []
        }
        
        # Classify and group recommendations
        for rec in recommendations:
            meal_type = rec['meal_type']
            if meal_type in meal_type_recommendations:
                # Add food details to recommendation
                food = Food.query.get(rec['food_id'])
                if food:
                    rec['food'] = food
                    meal_type_recommendations[meal_type].append(rec)
        
        # Sort each group by score
        for meal_type in meal_type_recommendations:
            meal_type_recommendations[meal_type] = sorted(
                meal_type_recommendations[meal_type],
                key=lambda x: x['total_score'],
                reverse=True
            )
            print(f"Found {len(meal_type_recommendations[meal_type])} items for {meal_type}")
        
        # Increase recommendations per meal type
        max_per_meal_type = {'Sarapan': 8, 'Makan Siang': 8, 'Makan Malam': 8, 'Cemilan': 8}
        selected_recommendations = []
        
        for meal_type, recs in meal_type_recommendations.items():
            count = min(max_per_meal_type[meal_type], len(recs))
            for rec in recs[:count]:
                selected_recommendations.append(rec)
        
        # Add the selected recommendations to the database
        for rec in selected_recommendations:
            new_rec = Recommendation(
                user_id=user_id,
                food_id=rec['food_id'],
                score=float(rec['total_score']),
                recommendation_date=current_date,
                food_status=rec['food_status'],
                meal_type=rec['meal_type']
            )
            db.session.add(new_rec)
        
        db.session.commit()
        print(f"Saved {len(selected_recommendations)} recommendations to database")

        # Prepare response structured by meal period
        daily_menu = {
            'breakfast': [],  # Sarapan
            'lunch': [],      # Makan Siang
            'dinner': [],     # Makan Malam
            'snacks': []      # Cemilan
        }

        # Map Indonesian meal types to keys in our response
        meal_type_mapping = {
            'Sarapan': 'breakfast',
            'Makan Siang': 'lunch',
            'Makan Malam': 'dinner',
            'Cemilan': 'snacks'
        }

        # Process the selected recommendations
        for rec in selected_recommendations:
            food = Food.query.get(rec['food_id'])
            if not food:
                continue
                
            recommendation = Recommendation.query.filter_by(
                user_id=user_id,
                food_id=food.id,
                recommendation_date=current_date
            ).first()
            
            if not recommendation:
                continue
            
            # Map Indonesian meal type to our response structure
            meal_key = meal_type_mapping.get(rec['meal_type'], 'snacks')
            
            # Add food to the daily menu
            food_info = {
                'id': food.id,
                'recommendation_id': recommendation.id,
                'name': food.name,
                'calories': food.caloric_value,
                'protein': food.protein,
                'carbs': food.carbohydrates,
                'fat': food.fat,
                'score': recommendation.score,
                'image_url': food.image_url,
                'food_status': rec['food_status']
            }
            
            daily_menu[meal_key].append(food_info)

        return jsonify(daily_menu), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error generating daily menu: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'message': f'Error: {str(e)}',
            'error_type': type(e).__name__
        }), 500


@bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Process user feedback for recommendations"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # Validate required fields
        if 'recommendation_id' not in data:
            return jsonify({'message': 'ID rekomendasi diperlukan'}), 400

        # Get recommendation with additional check
        recommendation = Recommendation.query.filter_by(
            id=data['recommendation_id'],
            user_id=user_id,
            recommendation_date=datetime.now().date()
        ).first()

        if not recommendation:
            return jsonify({'message': 'Rekomendasi tidak ditemukan'}), 404

        # Update recommendation feedback
        recommendation.is_consumed = data.get('is_consumed', False)
        recommendation.rating = data.get('rating')
        recommendation.feedback_date = datetime.utcnow()

        # Update recommender model if rating provided
        if data.get('rating'):
            recommender = HybridDietRecommender()
            recommender.update_weights(
                user_id=user_id,
                food_id=recommendation.food_id,
                rating=data['rating']
            )

        db.session.commit()

        # Return success and trigger menu refresh
        return jsonify({
            'message': 'Feedback berhasil disimpan',
            'should_refresh': True
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'message': f'Terjadi kesalahan: {str(e)}',
            'error_type': type(e).__name__
        }), 500


@bp.route('/diet-goals', methods=['GET'])
@jwt_required()
def get_diet_goals():
    """Get user's active diet goal"""
    try:
        user_id = get_jwt_identity()

        active_goal = DietGoal.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()

        if not active_goal:
            return jsonify({'has_active_goal': False}), 200

        return jsonify({
            'has_active_goal': True,
            'goal': {
                'id': active_goal.id,
                'medical_condition': active_goal.medical_condition,
                'target_weight': active_goal.target_weight,
                'target_date': active_goal.target_date.isoformat(),
                'status': active_goal.status,
                'created_at': active_goal.created_at.isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500