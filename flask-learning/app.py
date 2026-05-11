from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-only-change-me-before-deployment"

TOPICS = [
    {
        "id": 1,
        "category": "Web servers",
        "title": "What a web server does",
        "summary": "A server waits for HTTP requests, runs application logic, builds a response, sends it, then waits again.",
        "checkpoint": "Can you identify which part of a request-response cycle your code is handling?",
    },
    {
        "id": 2,
        "category": "Backend stack",
        "title": "Backend technologies",
        "summary": "A backend stack usually includes an operating system, language, web framework and database.",
        "checkpoint": "In this demo, the stack is Python, Flask, HTML templates, CSS and JavaScript.",
    },
    {
        "id": 3,
        "category": "Flask basics",
        "title": "Routes and endpoints",
        "summary": "Flask connects a URL pattern to a Python function using @app.route(...). The function return value becomes the HTTP response body.",
        "checkpoint": "Try /hello/Oliver to see a URL parameter passed into a Python function.",
    },
    {
        "id": 4,
        "category": "HTTP data",
        "title": "Reading request data",
        "summary": "Flask exposes URL query strings, form data and HTTP methods through request.args, request.form and request.method.",
        "checkpoint": "Try /concepts?category=Flask%20basics and inspect how the page changes.",
    },
    {
        "id": 5,
        "category": "Rendering",
        "title": "Server-side rendering with Jinja",
        "summary": "The server combines a template with data, then sends finished HTML to the browser.",
        "checkpoint": "Find the Jinja loop that renders the topic cards on the Concepts page.",
    },
    {
        "id": 6,
        "category": "Rendering",
        "title": "Client-side rendering with JavaScript",
        "summary": "The server can also send JSON to the browser. JavaScript can fetch that JSON and build part of the page in the browser.",
        "checkpoint": "Open the Client-side demo page and watch JavaScript populate the topic list.",
    },
    {
        "id": 7,
        "category": "Forms",
        "title": "Forms and POST requests",
        "summary": "Forms send user input to the server, commonly using POST. The server validates the data and returns or redirects to a response.",
        "checkpoint": "Submit the form with missing fields to see server-side validation.",
    },
    {
        "id": 8,
        "category": "Debugging",
        "title": "Debug mode and health checks",
        "summary": "During development, debug mode helps expose errors. A health endpoint gives a quick check that the app is running.",
        "checkpoint": "Visit /health and compare the plain text response with the template-rendered pages.",
    },
]

SERVER_CYCLE = [
    "Wait for an HTTP request from a client.",
    "Read request data such as the path, query string, form fields and method.",
    "Run server-side application logic.",
    "Render a template, return JSON, redirect, or send another response.",
    "Send the response to the client and wait for the next request.",
]

STACK = [
    {"name": "Python", "role": "Programming language for server logic"},
    {"name": "Flask", "role": "Micro-framework for routing and request handling"},
    {
        "name": "Jinja",
        "role": "Template engine used by Flask for server-side rendering",
    },
    {"name": "HTML", "role": "Page structure sent to the browser"},
    {"name": "CSS", "role": "Visual styling"},
    {"name": "JavaScript", "role": "Client-side interaction and JSON fetching"},
]


def get_topic_or_404(topic_id):
    for topic in TOPICS:
        if topic["id"] == topic_id:
            return topic
    abort(404)


@app.route("/")
def index():
    return render_template("index.html", topics=TOPICS[:4], stack=STACK)


@app.route("/concepts")
def concepts():
    selected_category = request.args.get("category", "All")
    categories = sorted({topic["category"] for topic in TOPICS})

    if selected_category == "All":
        filtered_topics = TOPICS
    else:
        filtered_topics = [
            topic for topic in TOPICS if topic["category"] == selected_category
        ]

    return render_template(
        "concepts.html",
        topics=filtered_topics,
        categories=categories,
        selected_category=selected_category,
    )


@app.route("/topic/<int:topic_id>")
def topic_detail(topic_id):
    topic = get_topic_or_404(topic_id)
    return render_template("topic_detail.html", topic=topic)


@app.route("/routes", methods=["GET", "POST"])
def routes_demo():
    submitted_name = None

    if request.method == "POST":
        submitted_name = request.form.get("name", "").strip()
        if submitted_name:
            return redirect(url_for("hello", name=submitted_name))
        flash("Enter a name before submitting the route demo form.", "error")

    return render_template(
        "routes_demo.html",
        submitted_name=submitted_name,
        query_args=dict(request.args),
        method=request.method,
    )


@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html", name=name)


@app.route("/forms", methods=["GET", "POST"])
def forms_demo():
    errors = []
    form_data = {"username": "", "role": "", "notes": ""}

    if request.method == "POST":
        form_data = {
            "username": request.form.get("username", "").strip(),
            "role": request.form.get("role", "").strip(),
            "notes": request.form.get("notes", "").strip(),
        }

        if len(form_data["username"]) < 2:
            errors.append("Username must be at least two characters long.")
        if not form_data["role"]:
            errors.append("Choose a role so the server has complete data.")

        if not errors:
            session["last_submission"] = form_data
            flash(
                "Form accepted. The server validated the POST data and stored it in the session.",
                "success",
            )
            return redirect(url_for("forms_demo"))

    return render_template(
        "forms_demo.html",
        errors=errors,
        form_data=form_data,
        last_submission=session.get("last_submission"),
    )


@app.route("/client-side")
def client_side():
    return render_template("client_side.html")


@app.route("/api/topics")
def api_topics():
    return jsonify(TOPICS)


@app.route("/api/server-cycle")
def api_server_cycle():
    return jsonify({"steps": SERVER_CYCLE})


@app.route("/health")
def health():
    return "OK: Flask app is running."


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
