from flask import Blueprint, current_app, render_template

from controllers import quota_summary


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html", current_page="index")


@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("signup.html", current_page="signup")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html", current_page="login")


@main_bp.route("/optimise", methods=["GET", "POST"])
def optimise():
    return render_template("optimise.html", current_page="optimise")


@main_bp.route("/community")
def community():
    return render_template("community.html", current_page="community")


@main_bp.route("/history")
def history():
    return render_template("history.html", current_page="history")


@main_bp.route("/dashboard")
def dashboard():
    quota = quota_summary(current_app.config["DAILY_PROMPT_QUOTA"])
    return render_template("dashboard.html", current_page="dashboard", quota=quota)


@main_bp.route("/profile", methods=["GET", "POST"])
def profile():
    return render_template("profile.html", current_page="profile")


@main_bp.route("/prompts/new", methods=["GET", "POST"])
def new_prompt():
    return render_template("prompt_form.html", current_page="new_prompt")
