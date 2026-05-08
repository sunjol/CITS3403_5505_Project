from pathlib import Path

from flask import Flask

from config import Config
from extensions import csrf, db, migrate
from routes import main_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    app.register_blueprint(main_bp)

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        print("Initialised the SQLite database.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
