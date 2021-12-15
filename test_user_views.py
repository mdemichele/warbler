"""User View Tests."""

import os 
from unittest import TestCase 
from models import db, connect_db, Message, User 

os.environ['DATABASE_URL'] = "postgresql:///warbler-test" 

from app import app, CURR_USER_KEY 

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False 

class UserViewTestCase(TestCase):
    """Test views for Users."""
    
    def setUp(self):
        """Create test client, add sample data."""
        User.query.delete()
        Message.query.delete()
        
        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()
        
    