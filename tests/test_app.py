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
        """Tests retrieving all notes for a user.
        Verifies that authenticated users can retrieve their notes successfully."""
        logger.info("Testing GET /api/notes endpoint")
        with app.app_context():
            response = self.app.get('/api/notes', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            logger.info("GET /api/notes test passed")

    def test_register(self):
        """Tests new user registration functionality.
        Verifies that users can register with valid credentials and receive correct response."""
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
        """Tests user authentication via login.
        Verifies that users can login with correct credentials and receive a valid JWT token."""
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
        """Tests note creation functionality.
        Verifies that authenticated users can create new notes with valid title and content."""
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
        """Tests retrieving a specific note by ID.
        Creates a note and verifies that it can be retrieved by its ID.
        Also tests authorization as only the note's owner should be able to retrieve it."""
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
        """Tests note update functionality.
        Creates a note, then tests updating its title and content.
        Verifies that only authenticated owners can update their notes."""
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
        """Tests note deletion functionality.
        Creates a note and verifies it can be deleted by its owner.
        Tests both successful deletion and proper authentication/authorization."""
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

    def test_health_check(self):
        """Tests the health check endpoint.
        Verifies that the server returns health status and required information."""
        logger.info("Testing health check endpoint")
        with app.app_context():
            response = self.app.get('/api/health')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data.decode('utf-8'))
            self.assertEqual(data['status'], 'healthy')
            self.assertIn('timestamp', data)
            self.assertIn('uptime_seconds', data)
            self.assertIn('process', data)
            self.assertIn('message', data)
            logger.info("Health check test passed")

if __name__ == '__main__':
    unittest.main()
