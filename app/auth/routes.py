"""Routes for the auth blueprint."""
from app.auth import bp


@bp.route('/login')
def login():
    """Placeholder login route."""
    return '<h1>Login</h1><p>Login form coming soon</p>'


@bp.route('/register')
def register():
    """Placeholder register route."""
    return '<h1>Register</h1><p>Register form coming soon</p>'


@bp.route('/logout')
def logout():
    """Placeholder logout route."""
    return '<h1>Logout</h1><p>Logout coming soon</p>'