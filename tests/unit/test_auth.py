import pytest

import controllers
from app import create_app
from extensions import db
from models import Prompt, User


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    DAILY_PROMPT_QUOTA = 10
    GROQ_API_KEY = None
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "test-model"
    GROQ_TIMEOUT_SECONDS = 1
    GROQ_USER_AGENT = "PromptShareTest/1.0"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def signup(client, username="test_user", email="test@example.com", password="Password1"):
    return client.post(
        "/signup",
        data={
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def test_signup_creates_user_with_hashed_password(client, app):
    response = signup(client)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="test_user").one()
        assert user.email == "test@example.com"
        assert user.password_hash != "Password1"
        assert user.check_password("Password1")


def test_signup_logs_user_in(client):
    response = signup(client)

    assert b"Your prompt dashboard" in response.data
    with client.session_transaction() as session:
        assert session["user_id"] is not None


def test_signup_rejects_duplicate_email(client):
    signup(client)
    client.post("/logout", follow_redirects=True)
    response = signup(client, username="second_user", email="test@example.com")

    assert b"That email is already registered." in response.data


def test_login_accepts_email_and_password(client):
    signup(client)
    client.post("/logout", follow_redirects=True)

    response = client.post(
        "/login",
        data={"identifier": "test@example.com", "password": "Password1"},
        follow_redirects=True,
    )

    assert b"Signed in successfully." in response.data
    assert b"Your prompt dashboard" in response.data


def test_login_rejects_bad_password(client):
    signup(client)
    client.post("/logout", follow_redirects=True)

    response = client.post(
        "/login",
        data={"identifier": "test@example.com", "password": "wrong-password"},
        follow_redirects=True,
    )

    assert b"Invalid username, email, or password." in response.data


def test_protected_page_redirects_to_login(client):
    response = client.get("/dashboard", follow_redirects=True)

    assert b"Please sign in to continue." in response.data
    assert b"Welcome Back" in response.data


def test_optimise_uses_local_model_by_default(client, app):
    signup(client)

    response = client.post(
        "/optimise",
        data={
            "goal": "Improve product copy",
            "prompt": "Write about headphones.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "General users",
            "focus": ["clarity", "constraints"],
        },
        follow_redirects=True,
    )

    assert b"Generated with Local fallback." in response.data
    with app.app_context():
        prompt = Prompt.query.filter_by(title="Improve product copy").one()
        assert prompt.original_prompt == "Write about headphones."
        assert "Role: Act as a precise prompt engineer." in prompt.optimised_prompt


def test_external_model_button_requires_groq_key(client):
    signup(client)

    response = client.post(
        "/optimise",
        data={
            "goal": "Improve product copy",
            "prompt": "Write about headphones.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "General users",
            "focus": ["clarity"],
            "use_external_model": "1",
        },
        follow_redirects=True,
    )

    assert b"Groq API key is not configured." in response.data


def test_external_model_block_falls_back_to_local(client, app, monkeypatch):
    signup(client)

    def blocked_groq(*args, **kwargs):
        raise controllers.ExternalModelError(
            "Groq blocked the external-model request with HTTP 403 / error 1010. "
            "The app used the local fallback optimiser instead."
        )

    monkeypatch.setattr("routes.optimise_prompt_with_groq", blocked_groq)

    response = client.post(
        "/optimise",
        data={
            "goal": "Improve blocked request",
            "prompt": "Write about headphones.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "General users",
            "focus": ["clarity"],
            "use_external_model": "1",
        },
        follow_redirects=True,
    )

    assert b"error 1010" in response.data
    assert b"Generated with Local fallback." in response.data
    with app.app_context():
        prompt = Prompt.query.filter_by(title="Improve blocked request").one()
        assert "External model fallback" in prompt.notes
