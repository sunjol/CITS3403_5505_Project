"""Selenium fixtures for the root Flask app."""
import importlib.util
import os
import sys
import threading
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.core.os_manager import ChromeType
from webdriver_manager.chrome import ChromeDriverManager

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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


class SeleniumTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///selenium_test.sqlite"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "selenium-test-secret-key"
    TIMEZONE = "Australia/Perth"
    DAILY_PROMPT_QUOTA = 20


@pytest.fixture(scope="module")
def live_server():
    app = create_app(SeleniumTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="seleniumuser", email="selenium@example.com")
        user.set_password("seleniumpass")
        db.session.add(user)
        db.session.commit()

    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=5555, use_reloader=False),
        daemon=True,
    )
    server_thread.start()
    time.sleep(2)

    yield "http://127.0.0.1:5555"

    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="module")
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")

    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    try:
        service = Service(
            driver_path or ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install()
        )
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as error:
        pytest.skip(f"ChromeDriver is unavailable for Selenium tests: {error}")

    driver.implicitly_wait(5)

    yield driver

    driver.quit()
