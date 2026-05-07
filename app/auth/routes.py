"""Routes for the auth blueprint."""
from flask import render_template, request, redirect, url_for, flash

from app import db
from app.auth import bp
from app.models import User


@bp.route('/login')
def login():
    """Render the login page."""
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Show the sign-up page (GET) or create a new user (POST)."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Basic validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html')

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another.', 'error')
            return render_template('auth/signup.html')

        # Create the new user
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')


@bp.route('/logout')
def logout():
    """Placeholder logout route."""
    return '<h1>Logout</h1><p>Coming soon</p>'