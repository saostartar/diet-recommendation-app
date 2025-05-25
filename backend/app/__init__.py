from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
import os

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    # Configure CORS with specific settings
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000"],  # Frontend URL
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.routes import auth, food, recommendation, profile, progress
    from app.commands import register_commands
    
    register_commands(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(food.bp)
    app.register_blueprint(recommendation.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(progress.bp)
    return app