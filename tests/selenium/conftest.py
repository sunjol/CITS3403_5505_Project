"""Selenium test fixtures: starts a live Flask server and a browser."""
import threading
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from app import create_app, db
from app.models import User
from config import Config


class SeleniumTestConfig(Config):
    """Config for Selenium tests — uses a temporary file-based SQLite DB."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///selenium_test.db'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'selenium-test-secret-key'


@pytest.fixture(scope='module')
def live_server():
    """Start the Flask server in a background thread for browser tests."""
    app = create_app(SeleniumTestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()
        # Create a known test user for login tests
        user = User(username='seleniumuser', email='selenium@example.com')
        user.set_password('seleniumpass')
        db.session.add(user)
        db.session.commit()

    # Start Flask in background thread
    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=5555, use_reloader=False)
    )
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Give server time to start

    yield 'http://127.0.0.1:5555'

    # Cleanup database after tests
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope='module')
def browser():
    """Launch a Chrome browser for Selenium tests."""
    options = Options()
    options.add_argument('--headless=new')  # Run without opening visible window
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,800')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)

    yield driver

    driver.quit()