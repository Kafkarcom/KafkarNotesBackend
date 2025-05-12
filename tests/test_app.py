import unittest
import json
import sys
sys.path.append(".")
from app import app, db

class AppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_notes(self):
        with app.app_context():
            response = self.app.get('/notes')
            self.assertEqual(response.status_code, 200)

    def test_create_note(self):
        with app.app_context():
            response = self.app.post('/notes', json={'title': 'Test Note', 'content': 'Test Content'})
            self.assertEqual(response.status_code, 201)

    def test_get_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/notes', json={'title': 'Test Note', 'content': 'Test Content'})
            self.assertEqual(create_response.status_code, 201)
        
            # Then get the note
            note_id = json.loads(create_response.data.decode('utf-8'))['id']
            response = self.app.get(f'/notes/{note_id}')
            self.assertEqual(response.status_code, 200)

    def test_update_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/notes', json={'title': 'Test Note', 'content': 'Test Content'})
            self.assertEqual(create_response.status_code, 201)
        
            # Then update the note
            note_id = json.loads(create_response.data.decode('utf-8'))['id']
            response = self.app.put(f'/notes/{note_id}', json={'title': 'Updated Note', 'content': 'Updated Content'})
            self.assertEqual(response.status_code, 200)

    def test_delete_note(self):
        with app.app_context():
            # First create a note
            create_response = self.app.post('/notes', json={'title': 'Test Note', 'content': 'Test Content'})
            self.assertEqual(create_response.status_code, 201)
        
            # Then delete the note
            note_id = json.loads(create_response.data.decode('utf-8'))['id']
            response = self.app.delete(f'/notes/{note_id}')
            self.assertEqual(response.status_code, 204)

if __name__ == '__main__':
    unittest.main()
