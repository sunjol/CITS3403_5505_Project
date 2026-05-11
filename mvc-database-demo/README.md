# MVC and Databases Demo

This small Flask app demonstrates the main teaching points from the MVC and Databases slides:

- MVC architecture
- Flask routes as controllers
- Jinja HTML templates as views
- Python model classes backed by SQLite
- SQLAlchemy ORM
- primary keys, foreign keys and relationships
- CRUD operations through HTTP routes
- database migrations with Flask-Migrate
- separate HTML, CSS, JavaScript and backend code

## File map

```text
mvc_database_demo/
├── app/
│   ├── __init__.py              # Creates Flask app, SQLAlchemy db and Flask-Migrate
│   ├── controllers.py           # Application logic for CRUD operations
│   ├── models.py                # ORM models: Student and ProjectGroup
│   ├── routes.py                # HTTP routes and JSON API endpoints
│   ├── templates/index.html     # View template
│   └── static/
│       ├── css/styles.css       # Separate CSS
│       └── js/app.js            # Separate browser JavaScript
├── config.py                    # SQLite configuration
├── requirements.txt
└── run.py                       # App entry point
```

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

flask --app run.py db init
flask --app run.py db migrate -m "Initial tables"
flask --app run.py db upgrade

flask --app run.py run --debug
```

Open the local URL printed by Flask.

## Add initial demo data

After the app is running, press **Reset demo data** on the page.

## What to point out while teaching

1. `models.py` contains the Model layer. Each class maps to a database table.
2. `index.html` and `styles.css` are the View layer. They display data to the user.
3. `routes.py` and `controllers.py` are the Controller layer. They receive input, call model logic and return responses.
4. `ProjectGroup.id` and `Student.id` are primary keys.
5. `Student.group_id` is a foreign key.
6. `Student.group` and `ProjectGroup.students` show ORM relationships.
7. The browser uses `fetch()` in `app.js` to call the backend API.
8. The API routes demonstrate create, read, update and delete.
9. Flask-Migrate creates versioned database migration scripts.

## Useful API routes

```text
GET    /api/groups             Read all groups and students
POST   /api/groups             Create a group
POST   /api/students           Create a student
PATCH  /api/students/<id>      Update a student
DELETE /api/students/<id>      Delete a student
POST   /api/reset              Reset teaching demo data
```
