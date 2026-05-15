"""Selenium end-to-end tests for the password change flow on the profile page.

These tests verify that:
1. A logged-in user can change their password via the profile page and
   subsequently log in with the new password.
2. The password change form correctly rejects an incorrect current password.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _signup(browser, live_server, username, email, password):
    """Helper: register a new user via the signup form."""
    browser.delete_all_cookies()
    browser.get(f"{live_server}/signup")
    browser.find_element(By.ID, "username").send_keys(username)
    browser.find_element(By.ID, "email").send_keys(email)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.ID, "confirm-password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "#signup-form button[type='submit']").click()
    WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))


def _login(browser, live_server, identifier, password):
    """Helper: log in via the login form."""
    browser.delete_all_cookies()
    browser.get(f"{live_server}/login")
    browser.find_element(By.ID, "login-identifier").send_keys(identifier)
    browser.find_element(By.ID, "login-password").send_keys(password)
    browser.find_element(By.CSS_SELECTOR, "#login-form button[type='submit']").click()


def _submit_password_change_form(browser, current, new, confirm):
    """Helper: fill in the password change form and submit it.
    
    The profile page has TWO forms (profile update + password change), both
    with action='profile'. We find the password form by its action hidden
    field value and submit it directly.
    """
    browser.find_element(By.ID, "current-password").send_keys(current)
    browser.find_element(By.ID, "new-password").send_keys(new)
    browser.find_element(By.ID, "confirm-password").send_keys(confirm)
    # Find the form containing the current-password field and submit it
    form = browser.find_element(By.ID, "current-password").find_element(By.XPATH, "./ancestor::form")
    form.submit()


class TestPasswordChangeFlow:
    """End-to-end tests for the change-password form on /profile."""

    def test_user_can_change_password_and_login_with_new_one(self, browser, live_server):
        """A logged-in user can change their password and then log in with the new one."""
        username = "pwchangeuser"
        email = "pwchange@example.com"
        old_password = "OldPass1234"
        new_password = "NewPass5678"

        # 1. Sign up (auto-redirects to dashboard)
        _signup(browser, live_server, username, email, old_password)

        # 2. Navigate to profile page
        browser.get(f"{live_server}/profile")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "current-password"))
        )

        # 3. Submit the change-password form
        _submit_password_change_form(browser, old_password, new_password, new_password)
        WebDriverWait(browser, 10).until(EC.url_contains("/profile"))

        # 4. Log out by POSTing to /logout (it only accepts POST, not GET)
        browser.execute_script(
            f"const f = document.createElement('form');"
            f"f.method = 'POST';"
            f"f.action = '{live_server}/logout';"
            f"const t = document.createElement('input');"
            f"t.name = 'csrf_token';"
            f"t.value = document.querySelector('meta[name=csrf-token]')?.content || '';"
            f"f.appendChild(t);"
            f"document.body.appendChild(f);"
            f"f.submit();"
        )
        WebDriverWait(browser, 10).until(
            lambda b: "/login" in b.current_url or "/" == b.current_url.replace(live_server, "")
        )

        # 5. Log in with the NEW password
        _login(browser, live_server, username, new_password)

        # 6. Verify we reached the dashboard (proves new password works)
        WebDriverWait(browser, 10).until(EC.url_contains("/dashboard"))
        assert "your prompt dashboard" in browser.page_source.lower()

    def test_password_change_rejects_wrong_current_password(self, browser, live_server):
        """Submitting the change-password form with the wrong current password should fail."""
        username = "wrongpwuser"
        email = "wrongpw@example.com"
        correct_password = "CorrectPass123"

        # 1. Sign up and reach dashboard
        _signup(browser, live_server, username, email, correct_password)

        # 2. Go to profile
        browser.get(f"{live_server}/profile")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "current-password"))
        )

        # 3. Submit with WRONG current password
        _submit_password_change_form(browser, "DefinitelyWrongPwd", "NewPass5678", "NewPass5678")

        # 4. Wait for the page to reload (POST -> redirect -> GET /profile)
        WebDriverWait(browser, 10).until(EC.url_contains("/profile"))

        # 5. Verify an error appears - either in a flash message or form-error-list
        page_source = browser.page_source.lower()
        assert ("current password" in page_source and 
                ("incorrect" in page_source or "wrong" in page_source or "invalid" in page_source)), \
            f"Expected error message about incorrect current password. Page contains: {page_source[:500]}"