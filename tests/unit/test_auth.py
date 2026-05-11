import pytest
import importlib.util
from datetime import timedelta
from pathlib import Path

import controllers
from config import Config
from extensions import db
from models import DailyQuotaUsage, Prompt, User

APP_MODULE_PATH = Path(__file__).resolve().parents[2] / "app.py"
APP_SPEC = importlib.util.spec_from_file_location("promptshare_root_app", APP_MODULE_PATH)
APP_MODULE = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(APP_MODULE)
create_app = APP_MODULE.create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    DAILY_PROMPT_QUOTA = 10
    TIMEZONE = "Australia/Perth"
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


def save_prompt(
    client,
    title="Reusable lesson planner",
    category="Study",
    prompt="Create a weekly lesson plan.",
    notes="Plan lessons with revision blocks.",
    visibility="public",
):
    return client.post(
        "/prompts/new",
        data={
            "title": title,
            "category": category,
            "prompt": prompt,
            "notes": notes,
            "visibility": visibility,
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


def test_logout_button_has_confirmation(client):
    response = signup(client)

    assert b"data-logout-confirm" in response.data
    assert b"Are you sure you want to log out?" in response.data


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


def test_groq_request_bypasses_proxy_environment(monkeypatch):
    recorded = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"Polished prompt"}}]}'

    class FakeOpener:
        def open(self, request, timeout):
            recorded["url"] = request.full_url
            recorded["timeout"] = timeout
            return FakeResponse()

    def fake_proxy_handler(proxies):
        recorded["proxies"] = proxies
        return object()

    def fake_build_opener(handler):
        recorded["handler"] = handler
        return FakeOpener()

    monkeypatch.setattr(controllers.urllib.request, "ProxyHandler", fake_proxy_handler)
    monkeypatch.setattr(controllers.urllib.request, "build_opener", fake_build_opener)

    result = controllers.optimise_prompt_with_groq(
        "Write about headphones.",
        api_key="test-key",
        api_url="https://api.groq.com/openai/v1/chat/completions",
        model="test-model",
        timeout=5,
        user_agent="PromptShareTest/1.0",
    )

    assert result == "Polished prompt"
    assert recorded["proxies"] == {}
    assert recorded["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert recorded["timeout"] == 5


def test_default_daily_quota_is_twenty():
    assert Config.DAILY_PROMPT_QUOTA == 20


def test_new_prompt_saves_public_prompt_for_owner(client, app):
    signup(client)

    response = save_prompt(client)

    assert b"Prompt saved as public." in response.data
    assert b"Reusable lesson planner" in response.data
    with app.app_context():
        prompt = Prompt.query.filter_by(title="Reusable lesson planner").one()
        assert prompt.is_public is True
        assert prompt.category == "Study"


def test_community_shows_other_users_public_prompts(client):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Public code reviewer",
        category="Coding",
        prompt="Review this diff.",
        visibility="public",
    )
    save_prompt(
        client,
        title="Private study helper",
        category="Study",
        prompt="Help me study privately.",
        visibility="private",
    )
    client.post("/logout", follow_redirects=True)
    signup(client, username="bob_user", email="bob@example.com")

    response = client.get("/community")

    assert b"Public code reviewer" in response.data
    assert b"Private study helper" not in response.data


def test_community_owner_can_filter_private_prompts(client):
    signup(client)
    save_prompt(
        client,
        title="Private interview coach",
        category="Writing",
        prompt="Prepare interview answers.",
        visibility="private",
    )

    response = client.get("/community?visibility=my")

    assert b"Private interview coach" in response.data
    assert b"Private" in response.data


def test_community_view_options_are_simplified(client):
    signup(client)

    response = client.get("/community")

    assert b">All</option>" in response.data
    assert b"Community Public Posts" in response.data
    assert b"My Posts" in response.data
    assert b"My public posts" not in response.data
    assert b"My private posts" not in response.data


def test_community_search_and_category_filters(client):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Python unit test helper",
        category="Coding",
        prompt="Write Python unit tests for this function.",
        visibility="public",
    )
    save_prompt(
        client,
        title="Marketing headline writer",
        category="Marketing",
        prompt="Write campaign headlines.",
        visibility="public",
    )
    client.post("/logout", follow_redirects=True)
    signup(client, username="bob_user", email="bob@example.com")

    response = client.get("/community?query=python&category=Coding")

    assert b"Python unit test helper" in response.data
    assert b"Marketing headline writer" not in response.data


def test_community_all_includes_public_posts_and_own_private_posts(client):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Alice public checklist",
        category="Coding",
        prompt="Review a pull request.",
        visibility="public",
    )
    client.post("/logout", follow_redirects=True)

    signup(client, username="bob_user", email="bob@example.com")
    save_prompt(
        client,
        title="Bob private plan",
        category="Study",
        prompt="Plan my private study week.",
        visibility="private",
    )

    response = client.get("/community?visibility=all")

    assert b"Alice public checklist" in response.data
    assert b"Bob private plan" in response.data


def test_community_posts_can_be_deleted_by_owner(client, app):
    signup(client)
    save_prompt(
        client,
        title="Delete me from community",
        category="Writing",
        prompt="Temporary prompt.",
        visibility="private",
    )
    with app.app_context():
        prompt_id = Prompt.query.filter_by(title="Delete me from community").one().id

    response = client.post(
        f"/prompts/{prompt_id}/delete",
        data={"next": "/community?visibility=my"},
        follow_redirects=True,
    )

    assert b"Deleted &#39;Delete me from community&#39;." in response.data
    with app.app_context():
        assert db.session.get(Prompt, prompt_id) is None


def test_user_cannot_delete_another_users_prompt(client, app):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Alice protected prompt",
        category="Writing",
        prompt="Do not delete this.",
        visibility="public",
    )
    with app.app_context():
        prompt_id = Prompt.query.filter_by(title="Alice protected prompt").one().id
    client.post("/logout", follow_redirects=True)
    signup(client, username="bob_user", email="bob@example.com")

    response = client.post(
        f"/prompts/{prompt_id}/delete",
        data={"next": "/community"},
        follow_redirects=True,
    )

    assert b"That prompt could not be found in your account." in response.data
    with app.app_context():
        assert db.session.get(Prompt, prompt_id) is not None


def test_optimise_similar_prefills_public_prompt(client, app):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Public rubric helper",
        category="Study",
        prompt="Create a marking rubric for a web app assignment.",
        visibility="public",
    )
    with app.app_context():
        prompt_id = Prompt.query.filter_by(title="Public rubric helper").one().id

    client.post("/logout", follow_redirects=True)
    signup(client, username="bob_user", email="bob@example.com")

    response = client.get(f"/optimise?similar_prompt_id={prompt_id}")

    assert b"Prompt loaded. Adjust the draft, then optimise it." in response.data
    assert b'value="Public rubric helper"' in response.data
    assert b"Create a marking rubric for a web app assignment." in response.data


def test_optimise_similar_does_not_prefill_other_users_private_prompt(client, app):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Private scholarship draft",
        category="Writing",
        prompt="Help me write a private scholarship statement.",
        visibility="private",
    )
    with app.app_context():
        prompt_id = Prompt.query.filter_by(title="Private scholarship draft").one().id

    client.post("/logout", follow_redirects=True)
    signup(client, username="bob_user", email="bob@example.com")

    response = client.get(f"/optimise?similar_prompt_id={prompt_id}")

    assert b"That prompt is private or no longer available." in response.data
    assert b"Private scholarship draft" not in response.data
    assert b"Help me write a private scholarship statement." not in response.data


def test_history_shows_only_current_users_prompts(client):
    signup(client, username="alice_user", email="alice@example.com")
    save_prompt(
        client,
        title="Alice private draft",
        category="Writing",
        prompt="Draft Alice's private prompt.",
        visibility="private",
    )
    client.post("/logout", follow_redirects=True)

    signup(client, username="bob_user", email="bob@example.com")
    save_prompt(
        client,
        title="Bob public draft",
        category="Study",
        prompt="Draft Bob's study prompt.",
        visibility="public",
    )

    response = client.get("/history")

    assert b"Bob public draft" in response.data
    assert b"Alice private draft" not in response.data


def test_history_filters_saved_and_optimised_prompts(client):
    signup(client)
    save_prompt(
        client,
        title="Saved lesson prompt",
        category="Study",
        prompt="Create a lesson plan.",
        visibility="private",
    )
    client.post(
        "/optimise",
        data={
            "goal": "Optimised product prompt",
            "prompt": "Write about headphones.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "General users",
            "focus": ["clarity"],
        },
        follow_redirects=True,
    )

    response = client.get("/history?type=optimised&query=product")

    assert b"Optimised product prompt" in response.data
    assert b"Saved lesson prompt" not in response.data


def test_history_can_update_prompt_visibility(client, app):
    signup(client)
    save_prompt(
        client,
        title="Shareable checklist",
        category="Coding",
        prompt="Make a checklist.",
        visibility="private",
    )
    with app.app_context():
        prompt = Prompt.query.filter_by(title="Shareable checklist").one()
        prompt_id = prompt.id
        assert prompt.is_public is False

    response = client.post(
        f"/prompts/{prompt_id}/visibility",
        data={"visibility": "public"},
        follow_redirects=True,
    )

    assert b"Prompt visibility updated to public." in response.data
    assert b"Shareable checklist" in response.data
    with app.app_context():
        prompt = Prompt.query.filter_by(title="Shareable checklist").one()
        assert prompt.is_public is True


def test_dashboard_recent_prompt_can_be_deleted(client, app):
    signup(client)
    save_prompt(
        client,
        title="Dashboard delete prompt",
        category="Coding",
        prompt="Remove from dashboard.",
        visibility="public",
    )
    with app.app_context():
        prompt_id = Prompt.query.filter_by(title="Dashboard delete prompt").one().id

    dashboard = client.get("/dashboard")
    assert b"Dashboard delete prompt" in dashboard.data
    assert b"Delete" in dashboard.data

    response = client.post(
        f"/prompts/{prompt_id}/delete",
        data={"next": "/dashboard"},
        follow_redirects=True,
    )

    assert b"Deleted &#39;Dashboard delete prompt&#39;." in response.data
    with app.app_context():
        assert db.session.get(Prompt, prompt_id) is None


def test_optimise_consumes_daily_quota_and_dashboard_shows_usage(client, app):
    signup(client)

    response = client.post(
        "/optimise",
        data={
            "goal": "Quota counted prompt",
            "prompt": "Write about a study planner.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "Students",
            "focus": ["clarity"],
        },
        follow_redirects=True,
    )

    assert b"Prompt optimised and saved to your history." in response.data
    with app.app_context():
        user = User.query.filter_by(username="test_user").one()
        usage = DailyQuotaUsage.query.filter_by(user_id=user.id).one()
        assert usage.used_count == 1

    dashboard = client.get("/dashboard")
    assert b"Used today" in dashboard.data
    assert b"<strong>1</strong>" in dashboard.data
    assert b"<strong>9</strong>" in dashboard.data


def test_quota_exhaustion_blocks_optimise_request(client, app):
    signup(client)
    with app.app_context():
        user = User.query.filter_by(username="test_user").one()
        usage_date, _ = controllers.quota_period(app.config["TIMEZONE"])
        db.session.add(
            DailyQuotaUsage(
                user_id=user.id,
                usage_date=usage_date,
                used_count=app.config["DAILY_PROMPT_QUOTA"],
            )
        )
        db.session.commit()

    response = client.post(
        "/optimise",
        data={
            "goal": "Blocked quota prompt",
            "prompt": "This should not be saved.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "Students",
            "focus": ["clarity"],
        },
        follow_redirects=True,
    )

    assert b"Daily prompt quota exhausted." in response.data
    with app.app_context():
        assert Prompt.query.filter_by(title="Blocked quota prompt").first() is None


def test_daily_quota_resets_for_new_local_date(client, app):
    signup(client)
    with app.app_context():
        user = User.query.filter_by(username="test_user").one()
        usage_date, _ = controllers.quota_period(app.config["TIMEZONE"])
        db.session.add(
            DailyQuotaUsage(
                user_id=user.id,
                usage_date=usage_date - timedelta(days=1),
                used_count=app.config["DAILY_PROMPT_QUOTA"],
            )
        )
        db.session.commit()

    response = client.post(
        "/optimise",
        data={
            "goal": "Fresh day prompt",
            "prompt": "This should be allowed today.",
            "tone": "Friendly",
            "format": "Bullet points",
            "audience": "Students",
            "focus": ["clarity"],
        },
        follow_redirects=True,
    )

    assert b"Prompt optimised and saved to your history." in response.data
    with app.app_context():
        user = User.query.filter_by(username="test_user").one()
        usage_date, _ = controllers.quota_period(app.config["TIMEZONE"])
        usage = DailyQuotaUsage.query.filter_by(user_id=user.id, usage_date=usage_date).one()
        assert usage.used_count == 1


def test_profile_updates_account_details(client, app):
    signup(client)

    response = client.post(
        "/profile",
        data={
            "action": "profile",
            "username": "updated_user",
            "email": "updated@example.com",
        },
        follow_redirects=True,
    )

    assert b"Profile updated successfully." in response.data
    with app.app_context():
        user = User.query.filter_by(username="updated_user").one()
        assert user.email == "updated@example.com"


def test_profile_changes_password(client):
    signup(client)

    response = client.post(
        "/profile",
        data={
            "action": "password",
            "current_password": "Password1",
            "new_password": "BetterPass2",
            "confirm_password": "BetterPass2",
        },
        follow_redirects=True,
    )

    assert b"Password updated successfully." in response.data
    client.post("/logout", follow_redirects=True)

    old_login = client.post(
        "/login",
        data={"identifier": "test@example.com", "password": "Password1"},
        follow_redirects=True,
    )
    assert b"Invalid username, email, or password." in old_login.data

    new_login = client.post(
        "/login",
        data={"identifier": "test@example.com", "password": "BetterPass2"},
        follow_redirects=True,
    )
    assert b"Signed in successfully." in new_login.data


def test_profile_rejects_wrong_current_password(client):
    signup(client)

    response = client.post(
        "/profile",
        data={
            "action": "password",
            "current_password": "wrong",
            "new_password": "BetterPass2",
            "confirm_password": "BetterPass2",
        },
        follow_redirects=True,
    )

    assert b"Current password is incorrect." in response.data
