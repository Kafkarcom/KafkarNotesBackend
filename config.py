# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/notes_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secret key for JWT
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    
    # Debug mode
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'