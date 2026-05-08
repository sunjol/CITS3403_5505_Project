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
flask --app app run
```

## Tests

```bash
pytest
```
