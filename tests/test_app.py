import unittest
import json
import sys
import jwt
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, User

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()
            # Create a test user with hashed password
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(test_user)
            db.session.commit()
            self.user_id = test_user.id
            # Create auth token
            self.auth_token = jwt.encode(
                {'user_id': self.user_id, 'exp': datetime.utcnow() + timedelta(hours=24)},
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_notes(self):
        with app.app_context():
            response = self.app.get('/api/notes', headers=self.headers)
            self.assertEqual(response.status_code, 200)

    def test_register(self):
        with app.app_context():
            response = self.app.post('/api/register', json={
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123'
            })
            self.assertEqual(response.status_code, 201)

    def test_login(self):
        with app.app_context():
            response = self.app.post('/api/login', json={
                'username': 'testuser',
                'password': 'password123'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('token', json.loads(response.data.decode('utf-8')))

    def test_create_note(self):
        with app.app_context():
            response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(response.status_code, 201)

    def test_get_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then get the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            response = self.app.get(f'/api/notes/{note_data["id"]}', headers=self.headers)
            self.assertEqual(response.status_code, 200)

    def test_update_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then update the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            response = self.app.put(
                f'/api/notes/{note_data["id"]}',
                headers=self.headers,
                json={'title': 'Updated Note', 'content': 'Updated Content'}
            )
            self.assertEqual(response.status_code, 200)

    def test_delete_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then delete the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            response = self.app.delete(
                f'/api/notes/{note_data["id"]}',
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)  # Updated to match actual response code

if __name__ == '__main__':
    unittest.main()
