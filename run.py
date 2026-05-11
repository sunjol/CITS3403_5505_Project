"""Entry point for running the active root Flask application."""
import importlib.util
from pathlib import Path


APP_MODULE_PATH = Path(__file__).with_name("app.py")
APP_SPEC = importlib.util.spec_from_file_location("promptshare_root_app", APP_MODULE_PATH)
APP_MODULE = importlib.util.module_from_spec(APP_SPEC)
APP_SPEC.loader.exec_module(APP_MODULE)

app = APP_MODULE.create_app()


if __name__ == "__main__":
    app.run(debug=True)
