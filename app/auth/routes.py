"""Routes for the auth blueprint.

This module defines all HTTP endpoints handled by the /auth/* URL prefix:

    GET/POST  /auth/login           -> login()
    GET/POST  /auth/register        -> register()
    GET       /auth/logout          -> logout()       [requires login]
    GET/POST  /auth/profile/<name>  -> profile()      [requires login]

Security overview:
- All form submissions include a CSRF token (Flask-WTF) automatically
  rendered via {{ form.hidden_tag() }} in the templates.
- Passwords are never stored in plaintext: User.set_password() uses
  scrypt hashing via werkzeug.security.
- Password verification uses User.check_password() which performs a
  constant-time comparison to prevent timing attacks.
- Session management is handled by Flask-Login; routes that require
  an authenticated user are decorated with @login_required.
- Already-authenticated users hitting /login or /register are
  redirected away to prevent accidental account creation/sign-in.

Templates rendered:
    auth/login.html
    auth/signup.html
    auth/profile.html
"""
from flask import render_template, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.auth import bp
from app.auth.forms import RegistrationForm, LoginForm, ChangePasswordForm
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Display the login page (GET) or authenticate the user (POST).

    GET behaviour:
        Renders the login form. If the user is already authenticated,
        redirects to the homepage to prevent confusion.

    POST behaviour:
        Validates the submitted form. If valid:
        - Looks up the user by username (the 'identifier' field).
        - Verifies the submitted password against the stored hash.
        - On success: starts a Flask-Login session, optionally with
          'remember me' for persistent cookies.
        - On failure: re-renders the form with an error flash message.

    Note on identifier field:
        Currently looks up users by username only. To support email
        login, query first by username then fall back to email.

    Returns:
        Rendered HTML for the login page (GET, or POST with errors)
        or a redirect to /home (POST success).
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.identifier.data).first()

        # Use a generic message to avoid revealing whether the username
        # exists. This prevents user enumeration via the login form.
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember.data)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Display the sign-up page (GET) or create a new user account (POST).

    GET behaviour:
        Renders the registration form. If the user is already authenticated,
        redirects to the homepage.

    POST behaviour:
        Validates the form (including the custom validate_username check
        in RegistrationForm that rejects taken usernames). On success:
        - Creates a new User with hashed password via set_password().
        - Commits to the database.
        - Redirects to the login page (intentionally does NOT auto-login;
          the user must demonstrate they know their password).

    Returns:
        Rendered HTML for the signup page (GET, or POST with errors)
        or a redirect to /auth/login (POST success).
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)  # scrypt hash with salt
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Log the user out and clear the Flask-Login session.

    Protected by @login_required: anonymous users hitting this URL are
    redirected to the login page. This is intentional - there's no
    meaningful action to take if the user isn't logged in.

    Returns:
        Redirect to the homepage with a success flash message.
    """
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))


@bp.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    """Display a user's profile page and handle password change submissions.

    Profile visibility:
        - Owners (the user whose profile this is) see email, ID, and the
          change-password form.
        - Visitors see only public information (username, ID).

    Password change flow (only for owners):
        1. User submits ChangePasswordForm with current and new passwords.
        2. Route verifies current_password matches the stored hash.
        3. If verified: hashes new password and commits to DB.
        4. If not verified: flashes error and re-renders the page.

    Args:
        username: The username from the URL (e.g. /auth/profile/alice).

    Returns:
        Rendered HTML for the profile page, or a redirect to the same
        profile page on successful password change (PRG pattern).

    Raises:
        404: If no user exists with the given username.
    """
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)

    # Only the profile owner can edit their own settings (e.g. password).
    is_owner = current_user.is_authenticated and current_user.username == username

    form = ChangePasswordForm()
    if is_owner and form.validate_on_submit():
        # Verify current password before allowing the change. This prevents
        # an attacker from changing the password if they gain temporary
        # access to a logged-in session (e.g. unattended laptop).
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/profile.html', user=user, form=form, is_owner=is_owner)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Password updated successfully.', 'success')
        # Use POST-Redirect-GET (PRG) to prevent form resubmission on refresh.
        return redirect(url_for('auth.profile', username=username))

    return render_template('auth/profile.html', user=user, form=form, is_owner=is_owner)