import unittest
import json
import sys
import jwt
import logging
from datetime import datetime, timedelta
import os
from werkzeug.security import generate_password_hash

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, db, User, setup_logging

# Setup test logger
logger = setup_logging(testing=True)

class AppTestCase(unittest.TestCase):
    def setUp(self):
        logger.info("Setting up test environment")
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/notes_db_test'
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.app = app.test_client()
        
        with app.app_context():
            logger.info("Creating database tables")
            db.create_all()
            
            # Create a test user with hashed password
            logger.info("Creating test user")
            test_user = User(
                username='testuser',
                email='test@example.com',
                password=generate_password_hash('password123', method='pbkdf2:sha256')
            )
            db.session.add(test_user)
            db.session.commit()
            self.user_id = test_user.id
            
            # Create auth token
            logger.debug("Generating authentication token for test user")
            self.auth_token = jwt.encode(
                {'user_id': self.user_id, 'exp': datetime.utcnow() + timedelta(hours=24)},
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )
            self.headers = {'Authorization': f'Bearer {self.auth_token}'}

    def tearDown(self):
        logger.info("Cleaning up test environment")
        with app.app_context():
            db.session.remove()
            db.drop_all()
        logger.info("Test cleanup complete")

    def test_get_notes(self):
        logger.info("Testing GET /api/notes endpoint")
        with app.app_context():
            response = self.app.get('/api/notes', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            logger.info("GET /api/notes test passed")

    def test_register(self):
        logger.info("Testing user registration")
        with app.app_context():
            test_data = {
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'password123'
            }
            logger.debug(f"Attempting to register user: {test_data['username']}")
            response = self.app.post('/api/register', json=test_data)
            self.assertEqual(response.status_code, 201)
            logger.info("User registration test passed")

    def test_login(self):
        logger.info("Testing user login")
        with app.app_context():
            test_data = {
                'username': 'testuser',
                'password': 'password123'
            }
            logger.debug(f"Attempting to login user: {test_data['username']}")
            response = self.app.post('/api/login', json=test_data)
            self.assertEqual(response.status_code, 200)
            self.assertIn('token', json.loads(response.data.decode('utf-8')))
            logger.info("User login test passed")

    def test_create_note(self):
        logger.info("Testing note creation")
        with app.app_context():
            test_note = {'title': 'Test Note', 'content': 'Test Content'}
            logger.debug(f"Attempting to create note: {test_note['title']}")
            response = self.app.post('/api/notes', 
                headers=self.headers,
                json=test_note
            )
            self.assertEqual(response.status_code, 201)
            logger.info("Note creation test passed")

    def test_get_note(self):
        logger.info("Testing get single note")
        with app.app_context():
            # First create a note
            logger.debug("Creating test note for retrieval")
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then get the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            logger.debug(f"Attempting to retrieve note with id: {note_data['id']}")
            response = self.app.get(f'/api/notes/{note_data["id"]}', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            logger.info("Get single note test passed")

    def test_update_note(self):
        logger.info("Testing note update")
        with app.app_context():
            # First create a note
            logger.debug("Creating test note for update")
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then update the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            logger.debug(f"Attempting to update note with id: {note_data['id']}")
            update_data = {'title': 'Updated Note', 'content': 'Updated Content'}
            response = self.app.put(
                f'/api/notes/{note_data["id"]}',
                headers=self.headers,
                json=update_data
            )
            self.assertEqual(response.status_code, 200)
            logger.info("Note update test passed")

    def test_delete_note(self):
        logger.info("Testing note deletion")
        with app.app_context():
            # First create a note
            logger.debug("Creating test note for deletion")
            create_response = self.app.post('/api/notes', 
                headers=self.headers,
                json={'title': 'Test Note', 'content': 'Test Content'}
            )
            self.assertEqual(create_response.status_code, 201)
            
            # Then delete the note
            note_data = json.loads(create_response.data.decode('utf-8'))
            logger.debug(f"Attempting to delete note with id: {note_data['id']}")
            response = self.app.delete(
                f'/api/notes/{note_data["id"]}',
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
            logger.info("Note deletion test passed")

if __name__ == '__main__':
    unittest.main()
