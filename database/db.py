"""Database initialization module"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the app context"""
    db.init_app(app)
    
    # Import models here to avoid circular imports
    from database.models import User, Note  # noqa
    
    # Create tables
    with app.app_context():
        db.create_all()
