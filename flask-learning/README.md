# Flask Learning Site

A small educational website that covers the web server, Flask, server-side rendering, routes, request data, Jinja templates, forms, JSON endpoints and client-side rendering concepts from the lecture slides.

## Tech used

- Flask
- HTML
- Jinja templates
- CSS
- JavaScript

No database and no WTForms are used, so the project stays focused on Flask, HTML, JS and CSS.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug
```

Then open:

```text
http://127.0.0.1:5000
```

## Pages to inspect

- `/` home page and server-cycle JSON fetch
- `/concepts` server-side rendered topic list
- `/concepts?category=Flask%20basics` query-string filtering
- `/topic/1` integer route parameter
- `/routes` GET and POST route demo
- `/hello/Oliver` dynamic URL parameter
- `/forms` POST form handling and validation
- `/client-side` JavaScript fetch and client-side rendering
- `/api/topics` JSON endpoint
- `/api/server-cycle` JSON endpoint
- `/health` plain text health check

## Files worth reading first

- `app.py`: Flask app, routes, endpoints, form handling and JSON APIs
- `templates/base.html`: shared layout and Jinja template inheritance
- `templates/concepts.html`: Jinja loops, conditionals and query-string filtering
- `templates/forms_demo.html`: plain HTML form rendered by the server
- `static/js/main.js`: fetches JSON and performs client-side rendering
- `static/css/styles.css`: page styling
