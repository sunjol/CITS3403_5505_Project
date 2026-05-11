"""Unit tests for the auth module."""

from extensions import db
from models import User


class TestPasswordHashing:
    """Tests for User password hashing methods."""

    def test_password_is_hashed(self, app):
        """Password should be stored as a hash, not plaintext."""
        with app.app_context():
            user = User(username='alice', email='alice@example.com')
            user.set_password('mysecret123')
            assert user.password_hash is not None
            assert user.password_hash != 'mysecret123'
            assert user.password_hash.startswith('scrypt:') or \
                   user.password_hash.startswith('pbkdf2:')

    def test_correct_password_verifies(self, app):
        """check_password should return True for the correct password."""
        with app.app_context():
            user = User(username='bob', email='bob@example.com')
            user.set_password('correct_password')
            assert user.check_password('correct_password') is True

    def test_wrong_password_rejected(self, app):
        """check_password should return False for a wrong password."""
        with app.app_context():
            user = User(username='charlie', email='charlie@example.com')
            user.set_password('correct_password')
            assert user.check_password('wrong_password') is False


class TestUserModel:
    """Tests for the User database model."""

    def test_user_can_be_saved(self, app):
        """A new user should be saved to the database with all fields."""
        with app.app_context():
            user = User(username='dave', email='dave@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            saved = User.query.filter_by(username='dave').first()
            assert saved is not None
            assert saved.email == 'dave@example.com'
            assert saved.id is not None


class TestRegistration:
    """Tests for the /signup route."""

    def test_duplicate_username_rejected(self, app, client):
        """Trying to register with an existing username should fail."""
        # First, create a user
        with app.app_context():
            user = User(username='taken', email='taken@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

        # Try to register the same username again
        response = client.post('/signup', data={
            'username': 'taken',
            'email': 'different@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        assert b'That username is already taken.' in response.data
