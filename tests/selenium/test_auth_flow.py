"""Selenium end-to-end tests for the auth module."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestSignupFlow:
    """End-to-end browser tests for the signup flow."""

    def test_user_can_sign_up_and_redirects_to_login(self, browser, live_server):
        """Filling out the signup form should create a user and redirect to login."""
        # Start with a clean session
        browser.delete_all_cookies()

        browser.get(f'{live_server}/auth/register')

        # Fill in the form
        browser.find_element(By.ID, 'username').send_keys('newselenuser')
        browser.find_element(By.ID, 'email').send_keys('newselen@example.com')
        browser.find_element(By.ID, 'password').send_keys('mypassword123')
        browser.find_element(By.ID, 'confirm_password').send_keys('mypassword123')

        # Submit
        browser.find_element(By.ID, 'submit').click()

        # Wait for redirect
        WebDriverWait(browser, 10).until(EC.url_contains('/auth/login'))

        # Verify we landed on login page with success message
        assert '/auth/login' in browser.current_url
        page_source = browser.page_source.lower()
        assert 'account created successfully' in page_source


class TestLoginFlow:
    """End-to-end browser tests for the login flow."""

    def test_valid_credentials_log_user_in(self, browser, live_server):
        """Submitting correct credentials should log the user in and redirect to home."""
        # Start with a clean session
        browser.delete_all_cookies()

        browser.get(f'{live_server}/auth/login')

        browser.find_element(By.ID, 'identifier').send_keys('seleniumuser')
        browser.find_element(By.ID, 'password').send_keys('seleniumpass')
        browser.find_element(By.ID, 'submit').click()

        # Wait for redirect to home
        WebDriverWait(browser, 10).until(
            lambda driver: driver.current_url.endswith('/') or '/auth/login' not in driver.current_url
        )

        # Verify welcome message appears
        page_source = browser.page_source.lower()
        assert 'welcome back' in page_source or 'logout' in page_source

    def test_invalid_credentials_show_error(self, browser, live_server):
        """Submitting wrong password should show an error message."""
        # Start with a clean session — log out from any previous test
        browser.delete_all_cookies()

        browser.get(f'{live_server}/auth/login')

        browser.find_element(By.ID, 'identifier').send_keys('seleniumuser')
        browser.find_element(By.ID, 'password').send_keys('wrongpassword')
        browser.find_element(By.ID, 'submit').click()

        # Wait a bit for the page to reload
        time.sleep(1)

        # Verify error message
        page_source = browser.page_source.lower()
        assert 'invalid username or password' in page_source
        # Verify still on login page
        assert '/auth/login' in browser.current_url