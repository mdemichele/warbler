"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
    
        self.client = app.test_client()
        
    def tearDown(self):
        """Rollback test client to previous session"""
        res = super().tearDown()
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        
    def test_user_repr(self):
        """Does the repr method work as expected?"""
        # Create User 
        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )
        
        # Add user to database session 
        db.session.add(u)
        db.session.commit()
        
        # Query the user 
        u = User.query.filter_by(email="test@test.com").first()
    
        # Check that user prints something that matches __repr__ string 
        self.assertIn("testuser, test@test.com>", u.__repr__())
        
    def test_is_following_true(self):
        """Does the is_following method work when u1 is following u2?"""
        # Add both users to the database session 
        u1 = User(email="test1@test.com", username="testuser1", password="HASHED_PASSWORD")
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD")
        
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        
        # Have u2 follow u1 
        u2.following.append(u1)
        db.session.commit()
        
        # Check the is_following method on u2 works correctly  
        self.assertEqual(True, u2.is_following(u1))
        
    def test_is_following_false(self):
        """Does the is_following method work when u1 is NOT following u2?"""
        # Add both users to the database session 
        u1 = User(email="test1@test.com", username="testuser1", password="HASHED_PASSWORD")
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD")
        
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        
        # Check that the is_following method successfully returns False 
        self.assertEqual(False, u2.is_following(u1))
        
    def test_is_followed_by_true(self):
        """Does the is_followed_by method work when u1 is followed by u2?"""
        # Add both users to the database session 
        u1 = User(email="test1@test.com", username="testuser1", password="HASHED_PASSWORD")
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD")
        
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        
        # Have u2 follow u1 
        u2.following.append(u1)
        db.session.commit()
        
        # Check the is_followed_by method on u1 works correctly 
        self.assertEqual(True, u1.is_followed_by(u2))
        
    def test_is_followed_by_false(self):
        """Does the is_followed_by method work when u1 is NOT followed by u2?"""
        # Add both users to the database session 
        u1 = User(email="test1@test.com", username="testuser1", password="HASHED_PASSWORD")
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD")
        
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        
        self.assertEqual(False, u2.is_followed_by(u2))
        
    def test_create_user_success(self):
        """Does User.create successfully create a new user?"""
        valid = User.signup("testUser", "test@test.email.com", "password", None)
        db.session.commit()
        
        self.assertEqual(1, len(User.query.all()))
        
    def test_create_user_fail(self):
        """Does User.create fail to create a new user if validations fail?"""
        invalid = User.signup(None, "email@email.com", "HASHED_PASSWORD", None)
        
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    ###########################
    # Authentication Tests 
    ##########################
    def test_authenticate_user_success(self):
        """Does User.authenticate successsfully return a user when given a valid username and password?"""
        # Create user and add to database 
        u1 = User.signup("testuser1", "test1@test.com", "HASHED_PASSWORD", None)
        
        db.session.commit()
        
        # authenticate user 
        user = User.authenticate("testuser1", "HASHED_PASSWORD")
        
        self.assertIsNotNone(user)
        self.assertEqual(user, u1)
        
    def test_authenticate_user_failure_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        # Create user and add to database 
        u1 = User.signup("testuser1", "test1@test.com", "HASHED_PASSWORD", None)
        db.session.commit()
        
        # Attemt to authenticate user 
        user = User.authenticate("wrongUsername", "HASHED_PASSWORD")
        self.assertEqual(False, user)
        
    def test_authenticate_user_failure_password(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""
        # Create user and add to database 
        u1 = User.signup("testuser1", "test1@test.com", "HASHED_PASSWORD", None)
        db.session.commit()
        
        # Attemt to authenticate user 
        user = User.authenticate("testuser1", "WRONG_PASSWORD")
        self.assertEqual(False, user)
        