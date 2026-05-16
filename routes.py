import re
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
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
    COMMUNITY_SORT_OPTIONS,
    COMMUNITY_VISIBILITY_OPTIONS,
    ExternalModelError,
    HISTORY_TYPE_OPTIONS,
    HISTORY_VISIBILITY_OPTIONS,
    PROMPT_CATEGORIES,
    community_prompts,
    consume_quota,
    ensure_quota_available,
    like_context_for_prompts,
    normalise_history_filters,
    normalise_community_filters,
    toggle_prompt_like as apply_prompt_like,
    optimise_prompt,
    optimise_prompt_with_groq,
    quota_usage_for_user,
    user_history_prompts,
)


main_bp = Blueprint("main", __name__)


def wants_json_response():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please sign in to continue.", "warning")
            next_url = request.full_path if request.query_string else request.path
            return redirect(url_for("main.login", next=next_url))
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
        "use_external_model": False,
        "optimised_prompt": None,
        "model_source": None,
    }

    if request.method == "GET":
        similar_prompt_id = request.args.get("similar_prompt_id", type=int)
        if similar_prompt_id:
            source_prompt = Prompt.query.filter(
                Prompt.id == similar_prompt_id,
                or_(Prompt.is_public.is_(True), Prompt.user_id == g.user.id),
            ).first()
            if source_prompt:
                context["goal"] = source_prompt.title
                context["draft_prompt"] = source_prompt.original_prompt
                flash("Prompt loaded. Adjust the draft, then optimise it.", "success")
            else:
                flash("That prompt is private or no longer available.", "warning")

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
                "use_external_model": request.form.get("use_external_model") == "1",
            }
        )

        if not context["goal"] or not prompt_text:
            flash("Please enter a goal and prompt before optimising.", "warning")
            return render_template("optimise.html", **context)

        use_external_model = context["use_external_model"]
        try:
            ensure_quota_available(
                g.user,
                current_app.config["DAILY_PROMPT_QUOTA"],
                current_app.config.get("TIMEZONE", "Australia/Perth"),
            )

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
            consume_quota(
                g.user,
                current_app.config["DAILY_PROMPT_QUOTA"],
                current_app.config.get("TIMEZONE", "Australia/Perth"),
            )
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
            consume_quota(
                g.user,
                current_app.config["DAILY_PROMPT_QUOTA"],
                current_app.config.get("TIMEZONE", "Australia/Perth"),
            )
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
    filters = normalise_community_filters(request.args, g.user)
    if g.user is None and request.args.get("visibility") == "private":
        flash("Please sign in to view your private prompts.", "warning")

    prompts = community_prompts(filters, g.user)
    like_context = like_context_for_prompts(prompts, g.user)
    return render_template(
        "community.html",
        current_page="community",
        prompts=prompts,
        filters=filters,
        visibility_options=COMMUNITY_VISIBILITY_OPTIONS,
        sort_options=COMMUNITY_SORT_OPTIONS,
        **like_context,
    )


@main_bp.post("/prompts/<int:prompt_id>/like")
@login_required
def toggle_prompt_like(prompt_id):
    prompt = Prompt.query.filter_by(id=prompt_id, is_public=True).first()
    if not prompt:
        message = "Only public prompts can be liked."
        if wants_json_response():
            return jsonify({"success": False, "message": message}), 404
        flash(message, "warning")
        return redirect(url_for("main.community"))

    try:
        liked, like_count = apply_prompt_like(g.user, prompt)
        db.session.commit()
        label = "liked" if liked else "unliked"
        message = f"You {label} '{prompt.title}'. It now has {like_count} like(s)."
        if wants_json_response():
            return jsonify(
                {
                    "success": True,
                    "liked": liked,
                    "like_count": like_count,
                    "prompt_id": prompt.id,
                    "message": message,
                }
            )
        flash(message, "success")
    except ValueError as error:
        db.session.rollback()
        if wants_json_response():
            return jsonify({"success": False, "message": str(error)}), 400
        flash(str(error), "warning")

    next_url = request.form.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("main.community"))


@main_bp.post("/prompts/<int:prompt_id>/delete")
@login_required
def delete_prompt(prompt_id):
    prompt = Prompt.query.filter_by(id=prompt_id, user_id=g.user.id).first()
    if not prompt:
        flash("That prompt could not be found in your account.", "warning")
        return redirect(url_for("main.dashboard"))

    title = prompt.title
    db.session.delete(prompt)
    db.session.commit()
    flash(f"Deleted '{title}'.", "success")

    next_url = request.form.get("next", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(url_for("main.dashboard"))


@main_bp.route("/history")
@login_required
def history():
    filters = normalise_history_filters(request.args)
    prompts = user_history_prompts(g.user, filters)
    like_context = like_context_for_prompts(prompts, g.user)
    return render_template(
        "history.html",
        current_page="history",
        prompts=prompts,
        filters=filters,
        type_options=HISTORY_TYPE_OPTIONS,
        visibility_options=HISTORY_VISIBILITY_OPTIONS,
        sort_options=COMMUNITY_SORT_OPTIONS,
        **like_context,
    )


@main_bp.post("/prompts/<int:prompt_id>/visibility")
@login_required
def update_prompt_visibility(prompt_id):
    prompt = Prompt.query.filter_by(id=prompt_id, user_id=g.user.id).first()
    if not prompt:
        flash("That prompt could not be found in your history.", "warning")
        return redirect(url_for("main.history"))

    visibility = request.form.get("visibility")
    if visibility not in {"public", "private"}:
        flash("Choose a valid visibility option.", "warning")
        return redirect(url_for("main.history"))

    prompt.is_public = visibility == "public"
    db.session.commit()
    flash(f"Prompt visibility updated to {visibility}.", "success")
    return redirect(url_for("main.history", visibility=visibility))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    quota = quota_usage_for_user(
        g.user,
        current_app.config["DAILY_PROMPT_QUOTA"],
        current_app.config.get("TIMEZONE", "Australia/Perth"),
    )
    user_prompts = Prompt.query.filter_by(user_id=g.user.id)
    stats = {
        "saved_prompts": user_prompts.count(),
        "public_prompts": user_prompts.filter(Prompt.is_public.is_(True)).count(),
        "optimised_prompts": user_prompts.filter(Prompt.optimised_prompt.isnot(None)).count(),
    }
    recent_prompts = (
        Prompt.query.filter_by(user_id=g.user.id)
        .order_by(Prompt.updated_at.desc())
        .limit(5)
        .all()
    )
    recent_activity = [
        f"{prompt.title} was {'optimised' if prompt.optimised_prompt else 'saved'} as {'public' if prompt.is_public else 'private'}."
        for prompt in recent_prompts[:3]
    ]
    return render_template(
        "dashboard.html",
        current_page="dashboard",
        quota=quota,
        stats=stats,
        recent_prompts=recent_prompts,
        recent_activity=recent_activity,
    )


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile_errors = []
    password_errors = []

    if request.method == "POST":
        action = request.form.get("action")

        if action == "profile":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()

            if not username:
                profile_errors.append("Username is required.")
            elif not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
                profile_errors.append("Username must be 3-20 characters and use letters, numbers, or underscores only.")

            if not email:
                profile_errors.append("Email is required.")
            elif not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
                profile_errors.append("Please enter a valid email address.")

            existing_user = User.query.filter(
                User.id != g.user.id,
                or_(User.username == username, User.email == email),
            ).first()
            if existing_user:
                if existing_user.username == username:
                    profile_errors.append("That username is already taken.")
                if existing_user.email == email:
                    profile_errors.append("That email is already registered.")

            if not profile_errors:
                g.user.username = username
                g.user.email = email
                db.session.commit()
                flash("Profile updated successfully.", "success")
                return redirect(url_for("main.profile"))

        elif action == "password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not g.user.check_password(current_password):
                password_errors.append("Current password is incorrect.")
            if len(new_password) < 8:
                password_errors.append("New password must be at least 8 characters.")
            if not any(char.isalpha() for char in new_password) or not any(char.isdigit() for char in new_password):
                password_errors.append("New password must include both letters and numbers.")
            if new_password != confirm_password:
                password_errors.append("New passwords do not match.")

            if not password_errors:
                g.user.set_password(new_password)
                db.session.commit()
                flash("Password updated successfully.", "success")
                return redirect(url_for("main.profile"))
        else:
            profile_errors.append("Choose a valid profile action.")

    return render_template(
        "profile.html",
        current_page="profile",
        profile_errors=profile_errors,
        password_errors=password_errors,
    )


@main_bp.route("/prompts/new", methods=["GET", "POST"])
@login_required
def new_prompt():
    values = {
        "title": "",
        "category": "",
        "prompt": "",
        "notes": "",
        "visibility": "public",
    }
    errors = []

    if request.method == "POST":
        values.update(
            {
                "title": request.form.get("title", "").strip(),
                "category": request.form.get("category", "").strip(),
                "prompt": request.form.get("prompt", "").strip(),
                "notes": request.form.get("notes", "").strip(),
                "visibility": request.form.get("visibility", "private"),
            }
        )

        if not values["title"]:
            errors.append("Prompt title is required.")
        elif len(values["title"]) > 160:
            errors.append("Prompt title must be 160 characters or fewer.")

        if values["category"] not in PROMPT_CATEGORIES:
            errors.append("Choose a valid category.")

        if not values["prompt"]:
            errors.append("Prompt text is required.")

        if values["visibility"] not in {"public", "private"}:
            errors.append("Choose whether the prompt is public or private.")

        if not errors:
            prompt = Prompt(
                user_id=g.user.id,
                title=values["title"],
                category=values["category"],
                original_prompt=values["prompt"],
                notes=values["notes"],
                is_public=values["visibility"] == "public",
            )
            db.session.add(prompt)
            db.session.commit()

            visibility_label = "public" if prompt.is_public else "private"
            flash(f"Prompt saved as {visibility_label}.", "success")
            return redirect(url_for("main.community", visibility=visibility_label))

    return render_template(
        "prompt_form.html",
        current_page="new_prompt",
        categories=PROMPT_CATEGORIES,
        values=values,
        errors=errors,
    )
