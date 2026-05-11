"""Selenium end-to-end tests for active auth routes."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TestSignupFlow:
    def test_user_can_sign_up_and_reach_dashboard(self, browser, live_server):
        browser.delete_all_cookies()
        browser.get(f"{live_server}/signup")

        browser.find_element(By.ID, "username").send_keys("newselenuser")
        browser.find_element(By.ID, "email").send_keys("newselen@example.com")
        browser.find_element(By.ID, "password").send_keys("mypassword123")
        browser.find_element(By.ID, "confirm-password").send_keys("mypassword123")
        browser.find_element(By.CSS_SELECTOR, "#signup-form button[type='submit']").click()

        WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))
        page_source = browser.page_source.lower()
        assert "your prompt dashboard" in page_source
        assert "log out" in page_source


class TestLoginFlow:
    def test_valid_credentials_log_user_in(self, browser, live_server):
        browser.delete_all_cookies()
        browser.get(f"{live_server}/login")

        browser.find_element(By.ID, "login-identifier").send_keys("seleniumuser")
        browser.find_element(By.ID, "login-password").send_keys("seleniumpass")
        browser.find_element(By.CSS_SELECTOR, "#login-form button[type='submit']").click()

        WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))
        assert "your prompt dashboard" in browser.page_source.lower()

    def test_invalid_credentials_show_error(self, browser, live_server):
        browser.delete_all_cookies()
        browser.get(f"{live_server}/login")

        browser.find_element(By.ID, "login-identifier").send_keys("seleniumuser")
        browser.find_element(By.ID, "login-password").send_keys("wrongpassword")
        browser.find_element(By.CSS_SELECTOR, "#login-form button[type='submit']").click()
        time.sleep(1)

        page_source = browser.page_source.lower()
        assert "invalid username, email, or password." in page_source
        assert "/login" in browser.current_url
