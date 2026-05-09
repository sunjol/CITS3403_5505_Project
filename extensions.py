from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import event


db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()


def configure_sqlite_engine(app):
    """Apply SQLite-only pragmas after Flask-SQLAlchemy creates the engine."""
    database_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not database_uri.startswith("sqlite"):
        return

    with app.app_context():
        engine = db.engine

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=TRUNCATE")
        cursor.close()
