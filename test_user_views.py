"""User View Tests."""

import os 
from unittest import TestCase 
from models import db, connect_db, Message, User, Follows 

os.environ['DATABASE_URL'] = "postgresql:///warbler-test" 

from app import app, CURR_USER_KEY 

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False 

class UserViewTestCase(TestCase):
    """Test views for Users."""
    
    def setUp(self):
        """Create test client, add sample data."""
        
        db.drop_all()
        db.create_all()
        
        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
                                    
        self.testuser.id = 9999
        
        # Create sample data before each test 
        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()
        
    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response 
    
    def test_show_users(self):
        """Can anybody see the users page?"""
        
        with self.client as client: 
            
            response = client.get('/users')
            
            self.assertEqual(response.status_code, 200)
    
    def test_show_queried_user(self):
        """Can anybody look for a specific user using the search bar?"""
        
        with self.client as client:
            response = client.get('/users?q=abc')
            
            self.assertEqual(response.status_code, 200)
        
    def test_show_user_details(self):
        """Can anybody see the user's details page?"""
        
        with self.client as client:
            response = client.get(f'/users/{self.testuser.id}')
            
            self.assertEqual(response.status_code, 200)
            
    def test_show_user_follows(self):
        """Can user see their following page"""
        # Create a follows instance 
        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.testuser.id)
        
        db.session.add(f1)
        db.session.commit()
        
        # Show user follows page 
        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
                
            response = client.get(f'/users/{self.testuser.id}/following')
            
            self.assertIn("@abc", str(response.data))
            
        
        
    
    