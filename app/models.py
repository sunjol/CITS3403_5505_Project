"""Database models for PromptShare."""
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    """A registered user of PromptShare.

    Attributes:
        id: Primary key.
        username: Unique, 3-20 chars, indexed for fast lookup.
        email: Unique, indexed for fast lookup.
        password_hash: scrypt hash of the user's password (never plaintext).
        created_at: UTC timestamp when the user account was created.

    Authentication:
        - Inherits from UserMixin to provide Flask-Login's required methods
          (is_authenticated, is_active, is_anonymous, get_id).
        - Use set_password() to hash a new password before storing.
        - Use check_password() to verify a candidate password.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def set_password(self, password):
        """Hash and store the user's password.

        Uses werkzeug's scrypt hashing with automatic salt generation.
        The resulting hash is safe to store in the database - no plaintext
        password is ever persisted.

        Args:
            password: The plaintext password to hash.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a candidate password against the stored hash.

        Uses werkzeug's constant-time comparison to prevent timing attacks
        that could leak information about the stored hash.

        Args:
            password: The plaintext password to check.

        Returns:
            True if the password matches the stored hash, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Tell Flask-Login how to load a user from a user_id.

    Uses SQLAlchemy 2.x style db.session.get() instead of the deprecated
    User.query.get() to avoid LegacyAPIWarning.
    """
    return db.session.get(User, int(user_id))