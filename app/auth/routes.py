"""Routes for the auth blueprint."""
from flask import render_template, request, redirect, url_for, flash, session

from app import db
from app.auth import bp
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show the login page (GET) or authenticate the user (POST)."""
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        # Basic validation
        if not identifier or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html')

        # Look up the user by username
        user = User.query.filter_by(username=identifier).first()

        # Check if user exists and password is correct
        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html')

        # Login successful — store user_id in session
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Show the sign-up page (GET) or create a new user (POST)."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/signup.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/signup.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose another.', 'error')
            return render_template('auth/signup.html')

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html')


@bp.route('/logout')
def logout():
    """Log the user out and clear the session."""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))