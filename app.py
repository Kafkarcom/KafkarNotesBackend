# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime as dt
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/notes_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.relationship('Note', backref='author', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Note(db.Model):
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Note {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Helper function for token verification
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    # Create new user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': dt.datetime.utcnow() + dt.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token}), 200

# Note routes
@app.route('/api/notes', methods=['GET'])
@token_required
def get_all_notes(current_user):
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return jsonify([note.to_dict() for note in notes]), 200

@app.route('/api/notes/<int:note_id>', methods=['GET'])
@token_required
def get_one_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found'}), 404
    
    return jsonify(note.to_dict()), 200

@app.route('/api/notes', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.get_json()
    
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    new_note = Note(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id
    )
    
    db.session.add(new_note)
    db.session.commit()
    
    return jsonify(new_note.to_dict()), 201

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']
    
    db.session.commit()
    
    return jsonify(note.to_dict()), 200

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found'}), 404
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'message': 'Note deleted'}), 200

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)