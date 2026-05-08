# AGENTS.md

## Project Summary

Build a university group web application that polishes AI prompts. Users can sign up, log in, optimise prompts, save prompt history, view selected public data from other users, and manage their account.

Main pages:

| Page | Purpose |
| --- | --- |
| `index` | Landing page and app introduction. |
| `signup` | New account creation. |
| `login` | Existing user login. |
| `optimise` | Main prompt polishing page. |
| `community` | Public/shared prompt data from other users. |
| `history` | User's previous prompt optimisations. |
| `dashboard` | User summary, recent activity, and daily quota usage. |
| `profile` | Account details and settings. |

## Learning Outcomes

The project must show that the team can:

1. Explain how modern internet data and services are delivered.
2. Explain how the selected web technologies fit together.
3. Build a client-side and server-side web application.

## Hard Application Requirements

The application must:

1. Use a client-server architecture.
2. Allow users to sign up, log in, and log out.
3. Persist user data between sessions.
4. Allow users to view data from other users in some controlled manner.
5. Be useful, engaging, and intuitive.
6. Be developed in a public GitHub repository.
7. Include the required `README.md`.
8. Follow the approved technology stack.
9. Follow MVC architecture with Flask, SQLAlchemy, SQLite, and Jinja.
10. Include database migrations when models change.
11. Include at least 5 unit tests and at least 5 Selenium tests.
12. Store passwords as salted hashes.
13. Use CSRF protection for forms.
14. Keep secrets, API keys, and local database files out of GitHub.

## Approved Core Technology Stack

Only these core technologies are allowed:

- HTML
- CSS (Bootstrap is allowed.)
- JavaScript
- jQuery
- Flask and lecture-approved Flask plugins
- AJAX or WebSockets
- SQLite
- SQLAlchemy
- Flask-Migrate
- Jinja templates
- Selenium for browser tests

## Prohibited Core Technologies

Do not use unapproved core technologies, including:

- React, Angular, Vue, Svelte, or similar frontend frameworks
- MySQL, PostgreSQL, MongoDB, Firebase as the main database, or similar database replacements
- Sass or SCSS directly
- Unapproved CSS frameworks
- Any framework that replaces Flask, Jinja, SQLAlchemy, SQLite, or the approved client stack

## Allowed Supporting Libraries

Libraries are allowed only when they provide non-core app-specific functionality, such as AI API access, graphs, dates, icons, fonts, or small utilities. They must not replace the approved stack.

## Architecture: MVC with Flask, SQLAlchemy, and SQLite

### Model Layer

Use SQLAlchemy models for database-backed entities.

Requirements:

1. Define models in `models.py` or a clear models package.
2. Each model class represents one table.
3. Use `db.Column` for columns, primary keys for unique rows, and foreign keys or `db.relationship()` for linked data.
4. Prefer SQLAlchemy ORM operations over raw SQL.
5. Use raw SQL only with a documented reason.
6. Keep model helper methods small.

Expected model candidates:

- `User`
- `Prompt` or `Optimisation`
- `SharedPrompt` or `CommunityPost`
- `DailyQuotaUsage`
- Optional: `Comment`, `Like`, or other community models

### View Layer

Use Jinja templates for user-facing pages.

Requirements:

1. Store templates in `templates/`.
2. Keep business logic out of templates.
3. Store CSS in `static/css/`.
4. Store JavaScript in `static/js/`.
5. Use template inheritance for shared layout.
6. Produce valid, semantic HTML.

### Controller Layer

Use Flask routes and controller or service functions to handle requests.

Requirements:

1. Keep routes in `routes.py` or a clear routes package.
2. Move larger logic into `controllers.py`, `services.py`, or helpers.
3. Route flow should be: receive request, validate input, call model/service logic, return template, redirect, or JSON.
4. Use normal CRUD operations for persistent data.

### Database and Migrations

Requirements:

1. Use SQLite for local development unless explicitly told otherwise.
2. Configure database settings in `config.py` or equivalent.
3. Do not hardcode database settings throughout the app.
4. Use Flask-Migrate for schema changes.
5. Do not manually delete and recreate the database as the normal workflow.
6. Keep migrations in sync with SQLAlchemy models.

### Feature Design Rule

Start from the user story. Nouns usually map to models, verbs to routes or service functions, and screens to templates or JSON responses.

## Daily Quota Usage Feature

The dashboard must show each authenticated user's daily prompt polishing quota.

Hard requirements:

1. Each polish request consumes quota.
2. Each user has an independent daily quota.
3. Quota resets at 12:00 am each day in the app's configured timezone, defaulting to `Australia/Perth`.
4. A user must not be able to submit a polish request after their daily quota is exhausted.
5. The dashboard must display the user's daily quota limit, used amount, remaining amount, and next reset time.
6. Quota usage must be persisted in the database.
7. Quota checks and quota increments must happen server-side, not only in JavaScript.
8. Failed validation requests must not consume quota.
9. The quota limit must be configurable in `config.py` or environment configuration.
10. Tests must cover quota consumption, quota exhaustion, and daily reset behaviour.

Implementation guidance:

- Use a `DailyQuotaUsage` model with `user_id`, `usage_date`, `used_count`, `created_at`, and `updated_at`.
- Add a unique constraint on `(user_id, usage_date)`.
- Treat a new local date as a fresh quota period rather than relying on a scheduled reset job.
- Increment quota in the same backend workflow that creates a prompt optimisation record.
- Use a service function such as `check_and_consume_quota(user)` to keep route handlers small.

## Recommended Repository Structure

```text
project-root/
├── app.py
├── config.py
├── models.py
├── routes.py
├── controllers.py
├── forms.py
├── requirements.txt
├── README.md
├── AGENTS.md
├── migrations/
├── tests/
│   ├── unit/
│   └── selenium/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── optimise.html
│   ├── community.html
│   ├── history.html
│   ├── dashboard.html
│   └── profile.html
└── static/
    ├── css/
    │   └── styles.css
    ├── js/
    │   └── main.js
    └── images/
```

Blueprints may be used if they genuinely improve organisation.

## README.md Requirements

`README.md` must include:

1. App purpose, design, and use.
2. A table with each member's UWA ID, name, and GitHub username.
3. Launch instructions.
4. Test instructions.

## Design Requirements

The app should be engaging, effective, and intuitive. Navigation must be clear, and the landing page must make the app's purpose obvious.

## HTML Requirements

Use valid, semantic, well-organised HTML with appropriate Jinja template inheritance.

## CSS Requirements

Use valid, maintainable, responsive CSS in `static/css/`. Use the selected approved CSS framework consistently.

## JavaScript Requirements

Use valid JavaScript in `static/js/` for meaningful validation, DOM manipulation, AJAX, or WebSocket behaviour. Do not use JavaScript to hide missing backend functionality.

## Flask Requirements

Keep Flask code formatted, organised, and split across routes, models, controllers/services, forms, and configuration. Route handlers must stay readable.

## Data Model Requirements

Use maintainable SQLAlchemy models, relationships where appropriate, migrations for schema changes, and safe handling of authentication data.

## Authentication and Session Requirements

Support sign-up, login, logout, protected pages, persistent user data, and ownership checks for user-owned records.

## Security Requirements

Store passwords as salted hashes, use CSRF protection, keep secrets out of source control, validate input server-side, and safely render user-generated content.

## Testing Requirements

Include at least 5 unit tests and 5 Selenium tests. Selenium tests must run against a live server.

Recommended test areas:

- Signup, login, and logout
- Prompt optimisation creation
- Daily quota usage, exhaustion, and reset
- Prompt history display
- Community visibility
- Permission checks
- Form validation
- Model behaviour

## Prompt Optimisation Requirements

Authenticated users must be able to enter a prompt, submit it for polishing, view the improved prompt, and save both the original and polished versions to the database.

If using an external AI API, keep keys out of source control, handle failures gracefully, and provide a fallback or mock mode so the app remains markable.

## Community Requirements

The `community` page must show intentionally public or shareable data from other users, such as shared prompts, examples, templates, comments, likes, or a showcase. Do not expose private user data.

## Coding Agent Rules

Coding agents must:

1. Preserve the approved technology stack.
2. Keep MVC separation clear.
3. Keep routes small and readable.
4. Add or update tests when behaviour changes.
5. Add migrations when models change.
6. Update `README.md` when setup, launch, or test commands change.
7. Keep secrets out of source control.
8. Avoid large unrelated rewrites.
9. Preserve assessment-required features.
10. Use Australian English in user-facing text, for example `optimise`.

## Definition of Done

A feature is done only when it works in the browser, follows the approved stack and MVC architecture, persists data correctly, handles invalid input, has relevant tests, preserves security, and does not break existing pages.

## Marking Checklist

Before submission, verify that:

1. All brief-required features are implemented.
2. Users can sign up, log in, and log out.
3. User data persists between sessions.
4. Users can view appropriate data from other users.
5. The design is engaging, effective, and intuitive.
6. HTML, CSS, JavaScript, and Flask code are valid and organised.
7. SQLAlchemy models and migrations are current.
8. Password hashing, CSRF protection, and secret handling are correct.
9. Daily quota tracking works and is visible on the dashboard.
10. There are at least 5 unit tests and 5 Selenium tests.
11. `README.md` contains all required information.
12. The public GitHub repository can be launched by following the README.
