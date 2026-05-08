import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'promptshare.sqlite'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.environ.get("APP_TIMEZONE", "Australia/Perth")
    DAILY_PROMPT_QUOTA = int(os.environ.get("DAILY_PROMPT_QUOTA", "10"))
