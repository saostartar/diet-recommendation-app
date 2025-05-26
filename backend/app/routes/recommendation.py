from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.food import Food
from app.models.recommendation import Recommendation, DietGoal, FoodPreference
from app.utils.hybrid_recommender import HybridDietRecommender
from app import db
from datetime import datetime, date
import random
from typing import List, Dict

bp = Blueprint('recommendation', __name__)

@bp.route('/preferences', methods=['GET', 'POST'])
@jwt_required()
def set_preferences():
    """Handle user food preferences."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        if request.method == 'GET':
            active_preferences = FoodPreference.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            diet_type_pref = None
            allergies_prefs = []
            
            for pref in active_preferences:
                if pref.preference_type in ['vegetarian', 'halal']:
                    diet_type_pref = pref.preference_type
                else:
                    allergies_prefs.append(pref.preference_type)

            return jsonify({
                'has_preferences': bool(active_preferences),
                'preferences': {
                    'diet_type': diet_type_pref if diet_type_pref else "",
                    'allergies': allergies_prefs
                }
            }), 200

        # POST request
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Request body tidak boleh kosong'}), 400

        # Deactivate old preferences
        FoodPreference.query.filter_by(user_id=user_id).update({'is_active': False})

        new_preferences_to_add = []
        
        # Save diet type
        diet_type_from_req = data.get('diet_type')
        if diet_type_from_req and diet_type_from_req in ['vegetarian', 'halal', 'general']:
            if diet_type_from_req != 'general':
                new_preferences_to_add.append(FoodPreference(
                    user_id=user_id,
                    preference_type=diet_type_from_req,
                    is_active=True
                ))

        # Save allergies
        allergies_from_req = data.get('allergies', [])
        valid_allergies = ['dairy_free', 'nut_free', 'seafood_free', 'egg_free', 'soy_free']
        for allergy in allergies_from_req:
            if allergy in valid_allergies:
                new_preferences_to_add.append(FoodPreference(
                    user_id=user_id,
                    preference_type=allergy,
                    is_active=True
                ))
        
        if new_preferences_to_add:
            db.session.add_all(new_preferences_to_add)
        
        db.session.commit()
        return jsonify({'message': 'Preferensi makanan berhasil disimpan'}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error di /preferences: {str(e)}")
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500

@bp.route('/diet-goals', methods=['GET', 'POST'])
@jwt_required()
def handle_diet_goals():
    """Handle user diet goals."""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'target_weight' not in data or 'target_date' not in data:
                return jsonify({'message': 'Target berat dan tanggal diperlukan'}), 400

            # Deactivate previous active goals
            DietGoal.query.filter_by(user_id=user_id, status='active').update({'status': 'abandoned'})

            new_goal = DietGoal(
                user_id=user_id,
                target_weight=float(data['target_weight']),
                target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date(),
                medical_condition=data.get('medical_condition', 'none'),
                status='active'
            )
            db.session.add(new_goal)
            db.session.commit()
            return jsonify({'message': 'Tujuan diet berhasil disimpan', 'goal_id': new_goal.id}), 201
        except ValueError:
            db.session.rollback()
            return jsonify({'message': 'Format data tidak valid'}), 400
        except Exception as e:
            db.session.rollback()
            print(f"Error di POST /diet-goals: {str(e)}")
            return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500
    
    # GET request
    try:
        active_goal = DietGoal.query.filter_by(user_id=user_id, status='active').order_by(DietGoal.created_at.desc()).first()
        if not active_goal:
            return jsonify({'has_active_goal': False, 'goal': None}), 200

        return jsonify({
            'has_active_goal': True,
            'goal': {
                'id': active_goal.id,
                'target_weight': active_goal.target_weight,
                'target_date': active_goal.target_date.isoformat(),
                'medical_condition': active_goal.medical_condition,
                'status': active_goal.status,
                'created_at': active_goal.created_at.isoformat()
            }
        }), 200
    except Exception as e:
        print(f"Error di GET /diet-goals: {str(e)}")
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500

@bp.route('/recommend/daily-menu', methods=['GET'])
@jwt_required()
def get_daily_menu():
    """Generate personalized daily menu with diverse recommendations."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Check for active diet goal
        active_goal = DietGoal.query.filter_by(user_id=user_id, status='active').order_by(DietGoal.created_at.desc()).first()
        if not active_goal:
            return jsonify({'message': 'Tujuan diet aktif tidak ditemukan. Harap tetapkan tujuan diet Anda terlebih dahulu.'}), 404

        # Get user preferences
        active_preferences_db = FoodPreference.query.filter_by(user_id=user_id, is_active=True).all()
        user_preference_types = [p.preference_type for p in active_preferences_db]

        print(f"User {user_id} preferences: {user_preference_types}")
        print(f"Medical condition: {active_goal.medical_condition}")

        # Configure items per meal type
        items_per_meal_type = {
            'Sarapan': 5,
            'Makan Siang': 5,
            'Makan Malam': 5,
            'Cemilan': 5
        }

        # Get diverse recommendations
        recommender = HybridDietRecommender()
        all_candidate_recs = recommender.get_recommendations(
            user=user,
            goal=active_goal,
            preferences=user_preference_types,
            total_initial_candidates=500,
            items_per_meal_type=items_per_meal_type
        )
        
        if not all_candidate_recs:
            return jsonify({'message': 'Tidak ada rekomendasi makanan yang dapat dihasilkan saat ini.'}), 200

        print(f"Generated {len(all_candidate_recs)} total recommendations")

        # Clear old recommendations for today
        current_date = date.today()
        Recommendation.query.filter_by(user_id=user_id, recommendation_date=current_date).delete()
        db.session.commit()

        # Organize by meal type
        meal_type_mapping = {
            'Sarapan': 'breakfast',
            'Makan Siang': 'lunch', 
            'Makan Malam': 'dinner',
            'Cemilan': 'snacks'
        }
        
        daily_menu_response = {key: [] for key in meal_type_mapping.values()}
        
        # Group recommendations by meal type
        meal_groups = {}
        for rec in all_candidate_recs:
            meal_type = rec['meal_type']
            if meal_type not in meal_groups:
                meal_groups[meal_type] = []
            meal_groups[meal_type].append(rec)

        # Process each meal type
        for meal_type_name, frontend_key in meal_type_mapping.items():
            meal_recs = meal_groups.get(meal_type_name, [])
            target_count = items_per_meal_type.get(meal_type_name, 5)
            
            print(f"{meal_type_name}: {len(meal_recs)} candidates, targeting {target_count}")
            
            # Ensure we have enough recommendations
            if len(meal_recs) < target_count:
                # Add some fallback recommendations if needed
                meal_recs.extend(_get_fallback_recommendations(
                    meal_type_name, target_count - len(meal_recs), user_preference_types
                ))
            
            # Take top recommendations for this meal
            selected_recs = meal_recs[:target_count]
            
            for rec_data in selected_recs:
                food_obj = rec_data['food_object']
                
                # Save to database
                new_db_rec = Recommendation(
                    user_id=user_id,
                    food_id=food_obj.id,
                    score=float(rec_data['total_score']),
                    recommendation_date=current_date,
                    meal_type=rec_data['meal_type']
                )
                db.session.add(new_db_rec)
                db.session.flush()  # Get ID

                # Format for response
                daily_menu_response[frontend_key].append({
                    'id': food_obj.id,
                    'recommendation_id': new_db_rec.id,
                    'name': food_obj.name,
                    'calories': round(food_obj.caloric_value, 1) if food_obj.caloric_value else 0,
                    'protein': round(food_obj.protein, 1) if food_obj.protein else 0,
                    'carbs': round(food_obj.carbohydrates, 1) if food_obj.carbohydrates else 0,
                    'fat': round(food_obj.fat, 1) if food_obj.fat else 0,
                    'score': round(rec_data['total_score'], 3),
                    'image_url': None,
                    'meal_type_debug': rec_data['meal_type'],
                    'medical_bonus': rec_data.get('medical_bonus', 0),
                    'is_vegetarian': food_obj.is_vegetarian,
                    'is_halal': food_obj.is_halal
                })

        db.session.commit()
        
        # Log final counts
        for meal_type, foods in daily_menu_response.items():
            print(f"Final {meal_type}: {len(foods)} foods")
        
        return jsonify(daily_menu_response), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error di /recommend/daily-menu: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}', 'error_type': type(e).__name__}), 500

def _get_fallback_recommendations(meal_type: str, count: int, preferences: List[str]) -> List[Dict]:
    """Get fallback recommendations when not enough diverse options available."""
    try:
        # Get foods that match meal type characteristics
        if meal_type == 'Sarapan':
            foods = Food.query.filter(
                Food.caloric_value.between(100, 300),
                Food.carbohydrates > 10
            ).limit(count * 2).all()
        elif meal_type == 'Cemilan':
            foods = Food.query.filter(
                Food.caloric_value.between(50, 150)
            ).limit(count * 2).all()
        else:  # Lunch/Dinner
            foods = Food.query.filter(
                Food.caloric_value.between(200, 500),
                Food.protein > 5
            ).limit(count * 2).all()
        
        # Filter by preferences
        filtered_foods = []
        recommender = HybridDietRecommender()
        for food in foods:
            if recommender._matches_preferences(food, preferences):
                filtered_foods.append({
                    'food_id': food.id,
                    'food_object': food,
                    'total_score': 0.5,  # Neutral score
                    'cf_score': 0.0,
                    'nutrition_score': 0.5,
                    'meal_type': meal_type,
                    'medical_bonus': 0.0
                })
        
        # Shuffle for variety
        random.shuffle(filtered_foods)
        return filtered_foods[:count]
        
    except Exception as e:
        print(f"Error getting fallback recommendations: {e}")
        return []

@bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """Process user feedback for recommendations."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if 'recommendation_id' not in data:
            return jsonify({'message': 'ID rekomendasi diperlukan'}), 400

        recommendation_id = data['recommendation_id']
        recommendation = Recommendation.query.get(recommendation_id)

        if not recommendation:
            return jsonify({'message': 'Rekomendasi tidak ditemukan'}), 404
        
        if recommendation.user_id != user_id:
            return jsonify({'message': 'Tidak diizinkan memberi feedback untuk rekomendasi ini'}), 403

        recommendation.is_consumed = data.get('is_consumed', recommendation.is_consumed)
        
        # Update rating if provided
        if data.get('rating') is not None:
            try:
                rating_val = int(data['rating'])
                if 1 <= rating_val <= 5:
                    recommendation.rating = rating_val
                else:
                    return jsonify({'message': 'Rating harus antara 1 dan 5'}), 400
            except ValueError:
                return jsonify({'message': 'Rating harus berupa angka'}), 400
        
        recommendation.feedback_date = datetime.utcnow()

        # Update recommender weights if rating provided
        if recommendation.rating is not None:
            recommender = HybridDietRecommender()
            recommender.update_weights(
                user_id=user_id,
                food_id=recommendation.food_id,
                rating=recommendation.rating
            )

        db.session.commit()

        return jsonify({
            'message': 'Feedback berhasil disimpan',
            'should_refresh': False
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error di /feedback: {str(e)}")
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}', 'error_type': type(e).__name__}), 500