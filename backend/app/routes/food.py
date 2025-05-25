from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.food import Food
from app import db
import pandas as pd
import re

bp = Blueprint('food', __name__)

# Add this helper function to validate and sanitize image URLs
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

@bp.route('/foods', methods=['GET'])
@jwt_required()
def get_foods():
    try:
        # Get query parameters with defaults
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        origin = request.args.get('origin', None)  # Add origin filter

        # Get current user from JWT token
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'message': 'Invalid token'}), 401

        # Base query
        query = Food.query

        # Filter by origin if specified
        if origin:
            query = query.filter_by(origin=origin)

        # Query foods with pagination
        foods = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        if not foods:
            return jsonify({'message': 'No foods found'}), 404

        # Format response
        response = {
            'foods': [{
                'id': food.id,
                'name': food.name,
                'calories': food.caloric_value,
                'protein': food.protein,
                'carbs': food.carbohydrates,
                'fat': food.fat,
                'origin': food.origin,
                'image_url': validate_image_url(food.image_url) if food.origin == 'indonesia' else None
            } for food in foods.items],
            'total_pages': foods.pages,
            'current_page': foods.page,
            'total_items': foods.total
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in get_foods: {str(e)}")
        return jsonify({'message': f'Error retrieving foods: {str(e)}'}), 500


@bp.route('/foods/<int:id>', methods=['GET'])
@jwt_required()
def get_food(id):
    food = Food.query.get_or_404(id)
    return jsonify({
        'id': food.id,
        'name': food.name,
        'origin': food.origin,
        'image_url': validate_image_url(food.image_url) if food.origin == 'indonesia' else None,
        'nutritional_info': {
            'calories': food.caloric_value,
            'protein': food.protein,
            'carbs': food.carbohydrates,
            'fat': food.fat,
            'fiber': food.dietary_fiber,
            'vitamins': {
                'a': food.vitamin_a,
                'c': food.vitamin_c,
                'd': food.vitamin_d,
                'e': food.vitamin_e
            },
            'minerals': {
                'calcium': food.calcium,
                'iron': food.iron,
                'potassium': food.potassium
            }
        }
    })


@bp.route('/foods/search', methods=['GET'])
@jwt_required()
def search_foods():
    try:
        query = request.args.get('q', '')
        origin = request.args.get('origin', None)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Base query
        food_query = Food.query.filter(Food.name.ilike(f'%{query}%'))

        # Filter by origin if specified
        if origin:
            food_query = food_query.filter_by(origin=origin)

        # Paginate results
        foods = food_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        response = {
            'foods': [{
                'id': food.id,
                'name': food.name,
                'calories': food.caloric_value,
                'protein': food.protein,
                'carbs': food.carbohydrates,
                'fat': food.fat,
                'origin': food.origin,
                'image_url': validate_image_url(food.image_url) if food.origin == 'indonesia' else None
            } for food in foods.items],
            'total_pages': foods.pages,
            'current_page': foods.page,
            'total_items': foods.total
        }

        return jsonify(response), 200

    except Exception as e:
        print(f"Error in search_foods: {str(e)}")
        return jsonify({'message': f'Error searching foods: {str(e)}'}), 500