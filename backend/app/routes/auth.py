from flask import Blueprint, request, jsonify
from app.models.user import User
from app import db
from flask_jwt_extended import create_access_token
import re

bp = Blueprint('auth', __name__)

def validate_registration_data(data):
    """Validate registration form data"""
    errors = []
    
    # Required fields
    required_fields = ['username', 'email', 'password', 'age', 'weight', 'height', 'gender', 'activity_level']
    for field in required_fields:
        if not data.get(field):
            errors.append(f'{field} wajib diisi')
    
    # Username validation
    username = data.get('username', '').strip()
    if username:
        if len(username) < 3:
            errors.append('Nama pengguna minimal 3 karakter')
        elif len(username) > 50:
            errors.append('Nama pengguna maksimal 50 karakter')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Nama pengguna hanya boleh mengandung huruf, angka, dan underscore')
    
    # Email validation
    email = data.get('email', '').strip()
    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append('Format email tidak valid')
        elif len(email) > 100:
            errors.append('Email maksimal 100 karakter')
    
    # Password validation
    password = data.get('password', '')
    if password:
        if len(password) < 8:
            errors.append('Kata sandi minimal 8 karakter')
        elif len(password) > 128:
            errors.append('Kata sandi maksimal 128 karakter')
        elif not re.search(r'[A-Za-z]', password):
            errors.append('Kata sandi harus mengandung minimal satu huruf')
        elif not re.search(r'\d', password):
            errors.append('Kata sandi harus mengandung minimal satu angka')
    
    # Age validation
    try:
        age = int(data.get('age', 0))
        if age < 12 or age > 100:
            errors.append('Usia harus antara 18-65 tahun')
    except (ValueError, TypeError):
        errors.append('Usia harus berupa angka yang valid')
    
    # Weight validation
    try:
        weight = float(data.get('weight', 0))
        if weight < 30 or weight > 300:
            errors.append('Berat badan harus antara 30-300 kg')
    except (ValueError, TypeError):
        errors.append('Berat badan harus berupa angka yang valid')
    
    # Height validation
    try:
        height = float(data.get('height', 0))
        if height < 100 or height > 250:
            errors.append('Tinggi badan harus antara 100-250 cm')
    except (ValueError, TypeError):
        errors.append('Tinggi badan harus berupa angka yang valid')
    
    # Gender validation
    gender = data.get('gender', '')
    if gender and gender not in ['M', 'F']:
        errors.append('Jenis kelamin harus dipilih (M atau F)')
    
    # Activity level validation
    activity_level = data.get('activity_level', '')
    valid_activity_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
    if activity_level and activity_level not in valid_activity_levels:
        errors.append('Tingkat aktivitas tidak valid')
    
    return errors

@bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'Data tidak boleh kosong'}), 400
        
        # Validate input data
        validation_errors = validate_registration_data(data)
        if validation_errors:
            return jsonify({
                'message': 'Data tidak valid',
                'errors': validation_errors
            }), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email'].strip().lower()).first():
            return jsonify({'message': 'Email sudah terdaftar'}), 400
            
        if User.query.filter_by(username=data['username'].strip()).first():
            return jsonify({'message': 'Nama pengguna sudah digunakan'}), 400
        
        # Create new user
        user = User(
            username=data['username'].strip(),
            email=data['email'].strip().lower(),
            age=int(data['age']),
            weight=float(data['weight']),
            height=float(data['height']),
            gender=data['gender'],
            activity_level=data['activity_level'],
            medical_condition=data.get('medical_condition', '').strip() or None
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'Pendaftaran berhasil'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500


@bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'message': 'Email dan kata sandi wajib diisi'}), 400
        
        user = User.query.filter_by(email=data['email'].strip().lower()).first()
        
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({'access_token': access_token}), 200
            
        return jsonify({'message': 'Email atau kata sandi salah'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Terjadi kesalahan server: {str(e)}'}), 500