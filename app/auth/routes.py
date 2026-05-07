"""Routes for the auth blueprint."""
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.auth import bp
from app.auth.forms import RegistrationForm, LoginForm
from app.models import User


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show the login page (GET) or authenticate the user (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.identifier.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'error')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=form.remember.data)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Show the sign-up page (GET) or create a new user (POST)."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/signup.html', form=form)


@bp.route('/logout')
@login_required
def logout():
    """Log the user out and clear the session."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))