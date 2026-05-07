"""Application factory for PromptShare."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

from config import Config

# Initialize extensions (without app — bound later in create_app)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'
login_manager.login_message_category = 'error'


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists (for SQLite database)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Import models so SQLAlchemy registers them
    from app import models  # noqa: F401

    return app