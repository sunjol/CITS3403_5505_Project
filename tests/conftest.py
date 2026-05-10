"""Shared pytest fixtures for the test suite."""
import sys
from pathlib import Path

# Add project root to sys.path so imports work for both blueprint and flat structures
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from app import create_app, db
from app.models import User
from config import Config


class TestConfig(Config):
    """Configuration for tests — uses an in-memory SQLite database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'


@pytest.fixture
def app():
    """Create a fresh Flask app for each test."""
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for sending requests to the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a sample test user for authentication tests."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user