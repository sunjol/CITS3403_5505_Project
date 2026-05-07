from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = "dev-only-change-me"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'app.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
