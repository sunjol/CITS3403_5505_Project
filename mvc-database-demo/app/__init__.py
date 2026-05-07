from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from config import Config

# The db object is the ORM entry point. Models will inherit from db.Model.
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Flask-Migrate can detect them.
    from app import models  # noqa: F401

    from app.routes import main
    app.register_blueprint(main)

    return app
