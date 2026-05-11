"""Shared pytest fixtures for the root Flask app."""
import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from extensions import db
from models import User


APP_MODULE_PATH = PROJECT_ROOT / "app.py"
APP_SPEC = importlib.util.spec_from_file_location("promptshare_root_app", APP_MODULE_PATH)
APP_MODULE = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(APP_MODULE)
create_app = APP_MODULE.create_app


class TestConfig(Config):
    """Configuration for tests - uses an in-memory SQLite database."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    TIMEZONE = "Australia/Perth"


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
