"""Auth blueprint for sign-in, sign-up, and logout."""
from flask import Blueprint

bp = Blueprint('auth', __name__)

from app.auth import routes