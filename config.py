import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_dotenv(path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'promptshare.sqlite'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TIMEZONE = os.environ.get("APP_TIMEZONE", "Australia/Perth")
    DAILY_PROMPT_QUOTA = int(os.environ.get("DAILY_PROMPT_QUOTA", "20"))
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_API_URL = os.environ.get(
        "GROQ_API_URL",
        "https://api.groq.com/openai/v1/chat/completions",
    )
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_TIMEOUT_SECONDS = int(os.environ.get("GROQ_TIMEOUT_SECONDS", "30"))
    GROQ_USER_AGENT = os.environ.get(
        "GROQ_USER_AGENT",
        "PromptShare/1.0 (Flask; CITS3403 project)",
    )
