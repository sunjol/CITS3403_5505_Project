"""Application factory for PromptShare."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Initialize extensions (without app — bound later in create_app)
db = SQLAlchemy()


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

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app