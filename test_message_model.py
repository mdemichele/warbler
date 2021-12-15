"""User Message Tests."""

# run these tests like:
#
#   python3 -m unittest test_message_model.py 

import os 
from unittest import TestCase 
from sqlalchemy import exc 

from models import db, User, Message, Follows 

os.environ['DATABASE_URL'] = "postgresql:///warbler-test" 

from app import app 

db.create_all()

class MessageModelTestCase(TestCase):
    """Test model for messages."""
    
    def setUp(self):
        """Create test client""" 
        
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        
        u1 = User.signup("testuser1", "test1@test.com", "HASHED_PASSWORD", None)
        u1.id = 9999
        db.session.commit()
        
        self.client = app.test_client()
        
    def tearDown(self):
        """Rollback test client to previous session"""
        res = super().tearDown()
        db.session.rollback()
        
    def test_message_model(self):
        """Successfully create a message instance"""
        message = Message(text="Test Message", user_id=9999)
        db.session.add(message)
        db.session.commit()
        
        messages = Message.query.all() 
        
        self.assertEqual(1, len(messages))