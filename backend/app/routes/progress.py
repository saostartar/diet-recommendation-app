from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.recommendation import DietGoal, Recommendation
from app.models.progress import WeightProgress
from app.models.food import Food
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('progress', __name__)

@bp.route('/progress/weight', methods=['GET', 'POST'])
@jwt_required()
def weight_progress():
    """Handle weight tracking"""
    try:
        user_id = get_jwt_identity()
        
        if request.method == 'GET':
            # Get last 30 days of weight data
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            progress_data = WeightProgress.query.filter(
                WeightProgress.user_id == user_id,
                WeightProgress.date >= thirty_days_ago
            ).order_by(WeightProgress.date.asc()).all()
            
            # Get starting weight (from user profile)
            user = User.query.get(user_id)
            
            # Get goal data
            goal = DietGoal.query.filter_by(
                user_id=user_id,
                status='active'
            ).first()
            
            return jsonify({
                'starting_weight': user.weight,
                'current_weight': progress_data[-1].weight if progress_data else user.weight,
                'target_weight': goal.target_weight if goal else None,
                'target_date': goal.target_date.isoformat() if goal else None,
                'progress': [
                    {
                        'date': p.date.isoformat(),
                        'weight': p.weight
                    } for p in progress_data
                ]
            }), 200
            
        # POST request
        data = request.get_json()
        
        # Check if entry for today exists
        today = datetime.utcnow().date()
        existing = WeightProgress.query.filter_by(
            user_id=user_id,
            date=today
        ).first()
        
        if existing:
            # Update existing entry
            existing.weight = float(data['weight'])
        else:
            # Create new entry
            new_progress = WeightProgress(
                user_id=user_id,
                date=today,
                weight=float(data['weight'])
            )
            db.session.add(new_progress)
        
        db.session.commit()
        return jsonify({'message': 'Berat badan berhasil diperbarui'}), 201
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

@bp.route('/progress/calories', methods=['GET'])
@jwt_required()
def calorie_consumption():
    """Get calorie consumption stats"""
    try:
        user_id = get_jwt_identity()
        days = int(request.args.get('days', 7))
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Get consumed food with ratings within date range
        consumed_data = db.session.query(
            func.date(Recommendation.feedback_date).label('date'),
            func.sum(Food.caloric_value).label('total_calories')
        ).join(
            Food, Recommendation.food_id == Food.id
        ).filter(
            Recommendation.user_id == user_id,
            Recommendation.is_consumed == True,
            func.date(Recommendation.feedback_date) >= start_date,
            func.date(Recommendation.feedback_date) <= end_date
        ).group_by(
            func.date(Recommendation.feedback_date)
        ).all()
        
        # Create result with all dates in range
        result = []
        current_date = start_date
        while current_date <= end_date:
            # Find if we have data for this date
            day_data = next((item for item in consumed_data if item.date == current_date), None)
            
            result.append({
                'date': current_date.isoformat(),
                'calories': day_data.total_calories if day_data else 0
            })
            current_date += timedelta(days=1)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

@bp.route('/progress/nutrition', methods=['GET'])
@jwt_required()
def nutrition_stats():
    """Get nutrition consumption stats for the week"""
    try:
        user_id = get_jwt_identity()
        
        # Calculate date range for the past week
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=6)  # Last 7 days
        
        # Get nutrition data for consumed food
        nutrition_data = db.session.query(
            func.sum(Food.protein).label('protein'),
            func.sum(Food.carbohydrates).label('carbs'),
            func.sum(Food.fat).label('fat')
        ).join(
            Recommendation, Food.id == Recommendation.food_id
        ).filter(
            Recommendation.user_id == user_id,
            Recommendation.is_consumed == True,
            func.date(Recommendation.feedback_date) >= start_date,
            func.date(Recommendation.feedback_date) <= end_date
        ).first()
        
        # Get daily averages
        return jsonify({
            'daily_average': {
                'protein': round(nutrition_data.protein / 7, 1) if nutrition_data.protein else 0,
                'carbs': round(nutrition_data.carbs / 7, 1) if nutrition_data.carbs else 0,
                'fat': round(nutrition_data.fat / 7, 1) if nutrition_data.fat else 0
            },
            'weekly_total': {
                'protein': round(nutrition_data.protein, 1) if nutrition_data.protein else 0,
                'carbs': round(nutrition_data.carbs, 1) if nutrition_data.carbs else 0,
                'fat': round(nutrition_data.fat, 1) if nutrition_data.fat else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

@bp.route('/progress/streak', methods=['GET'])
@jwt_required()
def streak_info():
    """Get user's consistency streak"""
    try:
        user_id = get_jwt_identity()
        
        # Get dates of food consumption
        consumption_dates = db.session.query(
            func.date(Recommendation.feedback_date).label('date')
        ).filter(
            Recommendation.user_id == user_id,
            Recommendation.is_consumed == True
        ).distinct().order_by(
            func.date(Recommendation.feedback_date).desc()
        ).all()
        
        # Calculate streak
        if not consumption_dates:
            return jsonify({'current_streak': 0, 'longest_streak': 0}), 200
            
        dates = [d.date for d in consumption_dates]
        
        # Calculate current streak
        current_streak = 1
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        if yesterday not in dates:
            current_streak = 0
        else:
            check_date = yesterday - timedelta(days=1)
            while check_date in dates:
                current_streak += 1
                check_date -= timedelta(days=1)
        
        # Calculate longest streak (simplified - would need more logic for a complete solution)
        date_set = set(dates)
        longest_streak = current_streak
        
        for date in sorted(dates):
            temp_streak = 1
            next_day = date + timedelta(days=1)
            
            while next_day in date_set:
                temp_streak += 1
                next_day += timedelta(days=1)
                
            longest_streak = max(longest_streak, temp_streak)
        
        return jsonify({
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500