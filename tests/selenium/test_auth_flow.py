"""Selenium end-to-end tests for active auth routes."""
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

        WebDriverWait(browser, 10).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".form-error-list"),
                "Invalid username",
            )
        )
        assert "invalid username, email, or password." in browser.page_source.lower()
        assert "/login" in browser.current_url


class TestNavigationAndFilters:
    def test_history_requires_login(self, browser, live_server):
        browser.delete_all_cookies()
        browser.get(f"{live_server}/history")

        WebDriverWait(browser, 10).until(EC.url_contains("/login"))
        assert "please sign in to continue." in browser.page_source.lower()

    def test_community_visibility_filter_is_available(self, browser, live_server):
        browser.delete_all_cookies()
        browser.get(f"{live_server}/community")

        visibility = browser.find_element(By.ID, "visibility")
        options = [
            option.text for option in visibility.find_elements(By.TAG_NAME, "option")
        ]

        assert options == ["Public", "Private"]
        assert "Category" not in browser.page_source
