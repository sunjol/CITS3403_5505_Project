"""Routes for the main blueprint."""
from app.main import bp


@bp.route('/')
def index():
    """Placeholder homepage."""
    return '<h1>PromptShare</h1><p>Flask is running!</p>'