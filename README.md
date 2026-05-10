# CITS3403_5505_Project

PromptShare is a Flask web application for polishing AI prompts, saving prompt history, and browsing intentionally shared community prompt examples.

## Project Structure

```text
project-root/
├── app.py
├── config.py
├── controllers.py
├── extensions.py
├── forms.py
├── models.py
├── routes.py
├── requirements.txt
├── migrations/
├── tests/
│   ├── selenium/
│   └── unit/
├── templates/
│   ├── base.html
│   ├── community.html
│   ├── dashboard.html
│   ├── history.html
│   ├── index.html
│   ├── login.html
│   ├── optimise.html
│   ├── profile.html
│   ├── prompt_form.html
│   └── signup.html
└── static/
    ├── css/
    ├── images/
    └── js/
```

## Team Members

| UWA ID | Name | GitHub username |
| --- | --- | --- |
| TODO | TODO | TODO |

## Launch

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flask --app app init-db
flask --app app run
```

## Optional Groq Model

The optimise page uses the local fallback by default. To enable the `Use Groq Model` button, add these values to a local `.env` file:

```text
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

The `.env` file is ignored by Git and must not be committed.

## Running Tests

The project uses pytest for both unit and Selenium tests.

**Run all tests:**
```bash
pytest -v
```

**Run only unit tests:**
```bash
pytest tests/test_auth.py -v
```

**Run only Selenium tests:**
```bash
pytest tests/selenium/ -v
```

### Prerequisites

- Google Chrome must be installed for Selenium tests (the `webdriver-manager` package auto-downloads matching ChromeDriver)
- Tests use an in-memory SQLite database — no setup required