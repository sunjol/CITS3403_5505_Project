"""Routes for the auth blueprint."""
from flask import render_template

from app.auth import bp


@bp.route('/login')
def login():
    """Render the login page."""
    return render_template('auth/login.html')


@bp.route('/register')
def register():
    """Render the sign-up page."""
    return render_template('auth/signup.html')


@bp.route('/logout')
def logout():
    """Placeholder logout route."""
    return '<h1>Logout</h1><p>Coming soon</p>'