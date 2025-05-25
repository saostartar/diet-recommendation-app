from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os

bp = Blueprint('profile', __name__)

@bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile data"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User tidak ditemukan'}), 404
            
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'weight': user.weight,
            'height': user.height,
            'gender': user.gender,
            'activity_level': user.activity_level,
            'medical_condition': user.medical_condition,
            'avatar_url': user.avatar_url,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

@bp.route('/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile data"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User tidak ditemukan'}), 404
            
        data = request.get_json()
        
        # Validate email uniqueness if email is being changed
        if data.get('email') and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'message': 'Email sudah terdaftar'}), 400
                
        # Validate username uniqueness if username is being changed
        if data.get('username') and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'message': 'Username sudah digunakan'}), 400
        
        # Update user fields
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.age = data.get('age', user.age)
        user.weight = data.get('weight', user.weight)
        user.height = data.get('height', user.height)
        user.gender = data.get('gender', user.gender)
        user.activity_level = data.get('activity_level', user.activity_level)
        user.medical_condition = data.get('medical_condition', user.medical_condition)
        
        db.session.commit()
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'age': user.age,
            'weight': user.weight,
            'height': user.height,
            'gender': user.gender,
            'activity_level': user.activity_level,
            'medical_condition': user.medical_condition,
            'avatar_url': user.avatar_url,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'message': 'Profil berhasil diperbarui'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

@bp.route('/profile/avatar', methods=['POST'])
@jwt_required()
def update_avatar():
    """Update user profile avatar"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User tidak ditemukan'}), 404
            
        if 'avatar' not in request.files:
            return jsonify({'message': 'Tidak ada file yang diunggah'}), 400
            
        file = request.files['avatar']
        
        if file.filename == '':
            return jsonify({'message': 'Tidak ada file yang dipilih'}), 400
            
        if file and allowed_file(file.filename):
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{user_id}_{timestamp}_{file.filename}")
            
            # Ensure upload directory exists
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Update user avatar_url in database
            base_url = request.host_url.rstrip('/')
            avatar_url = f"/static/avatars/{filename}"
            full_avatar_url = f"{base_url}{avatar_url}"
            user.avatar_url = avatar_url  # Store the relative URL in database
            db.session.commit()
            
            return jsonify({
                'message': 'Avatar berhasil diperbarui',
                'avatar_url': full_avatar_url
            }), 200
        else:
            return jsonify({'message': 'Format file tidak diizinkan'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Terjadi kesalahan: {str(e)}'}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS