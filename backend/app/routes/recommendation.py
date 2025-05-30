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
import traceback

bp = Blueprint('recommendation', __name__)

@bp.route('/preferences', methods=['GET', 'POST'])
@jwt_required()
def set_preferences():
    """Handle user food preferences."""
    try:
        user_id = get_jwt_identity()
        # user = User.query.get_or_404(user_id) # Tidak digunakan secara langsung di sini

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

        FoodPreference.query.filter_by(user_id=user_id).update({'is_active': False})

        new_preferences_to_add = []
        
        diet_type_from_req = data.get('diet_type')
        if diet_type_from_req and diet_type_from_req in ['vegetarian', 'halal', 'general']:
            if diet_type_from_req != 'general': 
                new_preferences_to_add.append(FoodPreference(
                    user_id=user_id,
                    preference_type=diet_type_from_req,
                    is_active=True
                ))

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
        traceback.print_exc()
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500

@bp.route('/diet-goals', methods=['GET', 'POST'])
@jwt_required()
def handle_diet_goals():
    """Handle user diet goals."""
    user_id = get_jwt_identity()
    # user = User.query.get_or_404(user_id) # Tidak digunakan secara langsung

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'target_weight' not in data or 'target_date' not in data:
                return jsonify({'message': 'Target berat dan tanggal diperlukan'}), 400

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
            traceback.print_exc()
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
        traceback.print_exc()
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500

@bp.route('/recommend/daily-menu', methods=['GET'])
@jwt_required()
def get_daily_menu():
    """Generate personalized daily menu with diverse recommendations."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        active_goal = DietGoal.query.filter_by(user_id=user_id, status='active').order_by(DietGoal.created_at.desc()).first()
        if not active_goal:
            return jsonify({'message': 'Tujuan diet aktif tidak ditemukan. Harap tetapkan tujuan diet Anda terlebih dahulu.'}), 404

        active_preferences_db = FoodPreference.query.filter_by(user_id=user_id, is_active=True).all()
        user_preference_types = [p.preference_type for p in active_preferences_db]

        items_per_meal_type = {
            'Sarapan': 10, 
            'Makan Siang': 10,
            'Makan Malam': 10,
            'Cemilan': 10 
        }

        recommender = HybridDietRecommender() 
        all_candidate_recs = recommender.get_recommendations(
            user=user,
            goal=active_goal,
            preferences=user_preference_types,
            total_initial_candidates=700, 
            items_per_meal_type=items_per_meal_type
        )
        
        if not all_candidate_recs:
            return jsonify({'message': 'Tidak ada rekomendasi makanan yang dapat dihasilkan saat ini. Coba sesuaikan preferensi Anda.'}), 200

        current_date = date.today()
        Recommendation.query.filter_by(user_id=user_id, recommendation_date=current_date).delete()
        db.session.commit()

        meal_type_mapping_frontend = { 
            'Sarapan': 'breakfast', 'Makan Siang': 'lunch', 
            'Makan Malam': 'dinner', 'Cemilan': 'snacks'
        }
        
        daily_menu_response = {key: [] for key in meal_type_mapping_frontend.values()}
        
        meal_groups = {} 
        for rec in all_candidate_recs:
            meal_type_from_rec = rec['meal_type'] 
            if meal_type_from_rec not in meal_groups:
                meal_groups[meal_type_from_rec] = []
            meal_groups[meal_type_from_rec].append(rec)

        for meal_type_db_name, frontend_key in meal_type_mapping_frontend.items():
            meal_recs_for_type = meal_groups.get(meal_type_db_name, [])
            target_count_for_meal = items_per_meal_type.get(meal_type_db_name, 5) 
            
            if len(meal_recs_for_type) < target_count_for_meal:
                needed_fallback = target_count_for_meal - len(meal_recs_for_type)
                fallback_recs = _get_fallback_recommendations(
                    meal_type_db_name, 
                    needed_fallback,
                    user_preference_types,
                    user 
                )
                meal_recs_for_type.extend(fallback_recs)
            
            selected_recs_for_meal = meal_recs_for_type[:target_count_for_meal]
            
            for rec_data in selected_recs_for_meal:
                food_obj = rec_data['food_object'] 
                
                new_db_rec = Recommendation(
                    user_id=user_id,
                    food_id=food_obj.id,
                    score=float(rec_data.get('total_score', 0.5)), 
                    recommendation_date=current_date,
                    meal_type=rec_data['meal_type'] 
                )
                db.session.add(new_db_rec)
                db.session.flush() 

                # --- REFINED PREPARATION LOGIC ---
                requires_preparation = True  # Default to needing preparation
                preparation_notes = "Info persiapan tidak jelas, anggap perlu diolah"

                if food_obj.food_status == 'Bahan Dasar':
                    requires_preparation = True
                    preparation_notes = "Bahan dasar, perlu diolah"
                elif food_obj.food_status == 'Tunggal':
                    requires_preparation = True
                    preparation_notes = "Perlu diolah"
                elif food_obj.food_status == 'Olahan':
                    if 'mentah' in food_obj.name.lower():
                        requires_preparation = True
                        preparation_notes = "Perlu diolah (mentah)"
                    else:
                        requires_preparation = False 
                        preparation_notes = "Umumnya siap saji"
                        # Consider adding nuance like: "Siap saji, mungkin perlu dipanaskan" if more data was available
                # If food_status is None or unexpected, the default from above applies.
                # --- END REFINED PREPARATION LOGIC ---

                daily_menu_response[frontend_key].append({
                    'id': food_obj.id, 
                    'recommendation_id': new_db_rec.id, 
                    'food_code': food_obj.food_code, 
                    'name': food_obj.name,
                    'caloric_value_kcal': round(food_obj.caloric_value, 1) if food_obj.caloric_value is not None else 0,
                    'protein_g': round(food_obj.protein, 1) if food_obj.protein is not None else 0,
                    'carbohydrates_g': round(food_obj.carbohydrates, 1) if food_obj.carbohydrates is not None else 0,
                    'fat_g': round(food_obj.fat, 1) if food_obj.fat is not None else 0,
                    'dietary_fiber_g': round(food_obj.dietary_fiber, 1) if food_obj.dietary_fiber is not None else 0, 
                    'food_status_from_db': food_obj.food_status, 
                    'food_group': food_obj.food_group, 
                    'meal_type_actual': rec_data['meal_type'], 
                    'score': round(rec_data.get('total_score', 0.5), 3),
                    'image_url': "https://placehold.co/300x200/EFEFEF/AAAAAA?text=Gambar+Tidak+Tersedia", 
                    'requires_preparation': requires_preparation,
                    'preparation_notes': preparation_notes,
                    'classification': { 
                        'is_vegetarian': food_obj.is_vegetarian,
                        'is_halal': food_obj.is_halal,
                        'contains_dairy': food_obj.contains_dairy,
                        'contains_nuts': food_obj.contains_nuts,
                        'contains_seafood': food_obj.contains_seafood,
                        'contains_eggs': food_obj.contains_eggs,
                        'contains_soy': food_obj.contains_soy,
                    }
                })

        db.session.commit()
        return jsonify(daily_menu_response), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error di /recommend/daily-menu: {str(e)}")
        traceback.print_exc() 
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}', 'error_type': type(e).__name__}), 500

def _get_fallback_recommendations(
    target_meal_type: str, 
    count: int, 
    preferences: List[str],
    user: User 
    ) -> List[Dict]:
    """Get fallback recommendations when not enough diverse options available."""
    try:
        # Get active diet goal to check medical condition
        active_goal = DietGoal.query.filter_by(user_id=user.id, status='active').first()
        medical_condition = active_goal.medical_condition if active_goal else 'none'
        
        query = Food.query.filter(Food.meal_type.ilike(f'%{target_meal_type}%'))
        
        # Apply medical condition specific calorie limits
        if medical_condition == 'obesity':
            # Stricter calorie limits for obesity
            if target_meal_type == 'Sarapan':
                query = query.filter(Food.caloric_value.between(80, 250))
            elif target_meal_type == 'Cemilan':
                query = query.filter(Food.caloric_value.between(30, 150))
            elif target_meal_type in ['Makan Siang', 'Makan Malam']:
                query = query.filter(Food.caloric_value.between(200, 350))
        elif medical_condition == 'diabetes':
            # Moderate calorie limits with carb consideration
            if target_meal_type == 'Sarapan':
                query = query.filter(Food.caloric_value.between(100, 300))
            elif target_meal_type == 'Cemilan':
                query = query.filter(Food.caloric_value.between(50, 200))
            elif target_meal_type in ['Makan Siang', 'Makan Malam']:
                query = query.filter(Food.caloric_value.between(250, 400))
            # Add carb filter
            query = query.filter(Food.carbohydrates <= 30)
        elif medical_condition == 'hypertension':
            # Standard calorie limits but focus on sodium
            if target_meal_type == 'Sarapan':
                query = query.filter(Food.caloric_value.between(100, 400))
            elif target_meal_type == 'Cemilan':
                query = query.filter(Food.caloric_value.between(50, 250))
            elif target_meal_type in ['Makan Siang', 'Makan Malam']:
                query = query.filter(Food.caloric_value.between(250, 500))
            # Add sodium filter
            query = query.filter(db.or_(Food.sodium.is_(None), Food.sodium <= 300))
        else:
            # Standard limits for no medical condition
            if target_meal_type == 'Sarapan':
                query = query.filter(Food.caloric_value.between(100, 500))
            elif target_meal_type == 'Cemilan':
                query = query.filter(Food.caloric_value.between(50, 350))
            elif target_meal_type in ['Makan Siang', 'Makan Malam']:
                query = query.filter(Food.caloric_value.between(250, 750))
        
        candidate_foods = query.limit(count * 5).all()
        
        # Additional filtering for medical conditions
        if medical_condition != 'none':
            filtered_candidates = []
            for food in candidate_foods:
                food_name_lower = food.name.lower()
                
                # Skip problematic foods based on medical condition
                skip_food = False
                
                if medical_condition == 'diabetes':
                    high_carb_keywords = ['tepung', 'gula', 'sirup', 'dodol', 'kue manis']
                    if any(keyword in food_name_lower for keyword in high_carb_keywords):
                        skip_food = True
                elif medical_condition == 'hypertension':
                    high_sodium_keywords = ['dendeng', 'asin', 'kering', 'keripik', 'abon', 'terasi']
                    if any(keyword in food_name_lower for keyword in high_sodium_keywords):
                        skip_food = True
                elif medical_condition == 'obesity':
                    high_cal_keywords = ['goreng', 'keripik', 'dendeng', 'rempeyek']
                    if any(keyword in food_name_lower for keyword in high_cal_keywords):
                        skip_food = True
                
                if not skip_food:
                    filtered_candidates.append(food)
            
            candidate_foods = filtered_candidates
        
        filtered_foods_for_fallback = []
        temp_recommender = HybridDietRecommender() 

        for food in candidate_foods:
            if temp_recommender._matches_preferences(food, preferences): 
                # Determine preparation requirements
                requires_preparation_fallback = True
                preparation_notes_fallback = "Info persiapan tidak jelas, anggap perlu diolah"

                if food.food_status == 'Bahan Dasar':
                    requires_preparation_fallback = True
                    preparation_notes_fallback = "Bahan dasar, perlu diolah"
                elif food.food_status == 'Tunggal':
                    requires_preparation_fallback = True
                    preparation_notes_fallback = "Perlu diolah"
                elif food.food_status == 'Olahan':
                    if 'mentah' in food.name.lower():
                        requires_preparation_fallback = True
                        preparation_notes_fallback = "Perlu diolah (mentah)"
                    else:
                        requires_preparation_fallback = False
                        preparation_notes_fallback = "Umumnya siap saji"
                
                # Adjust score based on medical condition suitability
                base_score = 0.35
                if medical_condition == 'obesity' and food.caloric_value and food.caloric_value < 200:
                    base_score = 0.45
                elif medical_condition == 'diabetes' and food.carbohydrates and food.carbohydrates < 15:
                    base_score = 0.45
                elif medical_condition == 'hypertension' and food.sodium and food.sodium < 200:
                    base_score = 0.45
                
                filtered_foods_for_fallback.append({
                    'food_id': food.id,
                    'food_object': food, 
                    'total_score': base_score,  
                    'cf_score': 0.0,
                    'nutrition_score': base_score, 
                    'meal_type': food.meal_type if food.meal_type and food.meal_type != 'Bahan Dasar' else target_meal_type, 
                    'medical_bonus': 0.0,
                    'requires_preparation': requires_preparation_fallback,
                    'preparation_notes': preparation_notes_fallback
                })
        
        random.shuffle(filtered_foods_for_fallback)
        return filtered_foods_for_fallback[:count]
        
    except Exception as e:
        print(f"Error getting fallback recommendations: {str(e)}")
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

        if recommendation.rating is not None:
            recommender = HybridDietRecommender()
            recommender.update_weights(
                user_id=user_id,
                food_id=recommendation.food_id,
                rating=recommendation.rating
            )

        db.session.commit()
        return jsonify({'message': 'Feedback berhasil disimpan', 'should_refresh': False }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error di /feedback: {str(e)}")
        traceback.print_exc()
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}', 'error_type': type(e).__name__}), 500