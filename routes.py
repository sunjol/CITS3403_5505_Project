from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_

from extensions import db
from forms import LoginForm, SignupForm
from models import Prompt, User
from controllers import (
    ExternalModelError,
    optimise_prompt,
    optimise_prompt_with_groq,
    quota_summary,
)


main_bp = Blueprint("main", __name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("main.login", next=request.path))
        return view_func(**kwargs)

    return wrapped_view


@main_bp.before_app_request
def load_current_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


@main_bp.app_context_processor
def inject_auth_context():
    return {"current_user": g.get("user")}


@main_bp.route("/")
def index():
    return render_template("index.html", current_page="index")


@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if g.user:
        return redirect(url_for("main.dashboard"))

    form = SignupForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        if existing_user:
            if existing_user.username == username:
                form.username.errors.append("That username is already taken.")
            if existing_user.email == email:
                form.email.errors.append("That email is already registered.")
        else:
            user = User(username=username, email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            flash("Account created. Welcome to PromptShare.", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("signup.html", current_page="signup", form=form)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        lookup = identifier.lower()
        user = User.query.filter(
            or_(User.username == identifier, User.email == lookup)
        ).first()

        if user and user.check_password(form.password.data):
            session.clear()
            session["user_id"] = user.id
            session.permanent = bool(form.remember.data)
            flash("Signed in successfully.", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("main.dashboard"))

        form.password.errors.append("Invalid username, email, or password.")

    return render_template("login.html", current_page="login", form=form)


@main_bp.post("/logout")
def logout():
    session.clear()
    flash("You have signed out.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/optimise", methods=["GET", "POST"])
@login_required
def optimise():
    context = {
        "current_page": "optimise",
        "goal": "",
        "draft_prompt": "Write a product description for my headphones.",
        "tone": "Clear and professional",
        "output_format": "Structured sections",
        "audience": "General users",
        "selected_focus": ["clarity", "constraints"],
        "optimised_prompt": None,
        "model_source": None,
    }

    if request.method == "POST":
        prompt_text = request.form.get("prompt", "").strip()
        context.update(
            {
                "goal": request.form.get("goal", "").strip(),
                "draft_prompt": prompt_text,
                "tone": request.form.get("tone", "Clear and professional"),
                "output_format": request.form.get("format", "Structured sections"),
                "audience": request.form.get("audience", "General users"),
                "selected_focus": request.form.getlist("focus"),
            }
        )

        if not context["goal"] or not prompt_text:
            flash("Please enter a goal and prompt before optimising.", "warning")
            return render_template("optimise.html", **context)

        use_external_model = request.form.get("use_external_model") == "1"
        try:
            if use_external_model:
                optimised_prompt = optimise_prompt_with_groq(
                    prompt_text,
                    api_key=current_app.config["GROQ_API_KEY"],
                    api_url=current_app.config["GROQ_API_URL"],
                    model=current_app.config["GROQ_MODEL"],
                    timeout=current_app.config["GROQ_TIMEOUT_SECONDS"],
                    user_agent=current_app.config["GROQ_USER_AGENT"],
                    tone=context["tone"],
                    output_format=context["output_format"],
                    audience=context["audience"],
                    focus=context["selected_focus"],
                )
                context["model_source"] = f"Groq: {current_app.config['GROQ_MODEL']}"
            else:
                optimised_prompt = optimise_prompt(
                    prompt_text,
                    tone=context["tone"],
                    output_format=context["output_format"],
                    audience=context["audience"],
                    focus=context["selected_focus"],
                )
                context["model_source"] = "Local fallback"

            prompt = Prompt(
                user_id=g.user.id,
                title=context["goal"],
                category="Optimisation",
                original_prompt=prompt_text,
                optimised_prompt=optimised_prompt,
                notes=f"Tone: {context['tone']}; Format: {context['output_format']}; Audience: {context['audience']}",
                is_public=False,
            )
            db.session.add(prompt)
            db.session.commit()

            context["optimised_prompt"] = optimised_prompt
            flash("Prompt optimised and saved to your history.", "success")
        except ExternalModelError as error:
            db.session.rollback()
            optimised_prompt = optimise_prompt(
                prompt_text,
                tone=context["tone"],
                output_format=context["output_format"],
                audience=context["audience"],
                focus=context["selected_focus"],
            )
            prompt = Prompt(
                user_id=g.user.id,
                title=context["goal"],
                category="Optimisation",
                original_prompt=prompt_text,
                optimised_prompt=optimised_prompt,
                notes=f"Tone: {context['tone']}; Format: {context['output_format']}; Audience: {context['audience']}; External model fallback",
                is_public=False,
            )
            db.session.add(prompt)
            db.session.commit()

            context["model_source"] = "Local fallback"
            context["optimised_prompt"] = optimised_prompt
            flash(str(error), "warning")
        except (RuntimeError, ValueError) as error:
            db.session.rollback()
            flash(str(error), "error")

    return render_template("optimise.html", **context)


@main_bp.route("/community")
def community():
    return render_template("community.html", current_page="community")


@main_bp.route("/history")
@login_required
def history():
    return render_template("history.html", current_page="history")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    quota = quota_summary(current_app.config["DAILY_PROMPT_QUOTA"])
    return render_template("dashboard.html", current_page="dashboard", quota=quota)


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    return render_template("profile.html", current_page="profile")


@main_bp.route("/prompts/new", methods=["GET", "POST"])
@login_required
def new_prompt():
    return render_template("prompt_form.html", current_page="new_prompt")
