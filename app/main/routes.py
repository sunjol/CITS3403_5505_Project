"""Routes for the main blueprint."""
from flask import render_template

from app.main import bp


@bp.route('/')
def index():
    """Render the homepage."""
    return render_template('main/index.html')