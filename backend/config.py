from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'sadjfdsahfjkashjfshdkjfhsakjdhfkjsadhfkjsadhfjkhsadkjfhkjsadhfkj'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
