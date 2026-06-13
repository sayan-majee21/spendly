# Spendly - Expense Tracker Project Instructions

## Project Overview
**Spendly** is a Flask-based web application designed as an educational tool for learning web development and database management. It allows users to track their personal expenses through a clean, modern interface.

### Core Technologies
- **Backend:** [Flask](https://flask.palletsprojects.com/) (v3.1.3+)
- **Database:** SQLite (Relational database for users and expenses)
- **Frontend:** Jinja2 Templates, Vanilla CSS, and Vanilla JavaScript
- **Testing:** [pytest](https://docs.pytest.org/) and `pytest-flask`
- **Design:** Modern "Paper & Ink" aesthetic using Google Fonts (*DM Serif Display*, *DM Sans*)

### Architecture
The project follows a standard Flask directory structure:
- `app.py`: Entry point, route definitions, and application logic.
- `database/`: Database connection and schema management (`db.py`).
- `templates/`: HTML layouts and page-specific templates extending `base.html`.
- `static/`: Client-side assets (CSS and JS).

## Building and Running
The following commands are used to manage the development environment:

### Environment Setup
1.  **Create Virtual Environment:** `python -m venv venv`
2.  **Activate Environment:** 
    - Windows: `.\venv\Scripts\activate`
    - Unix/macOS: `source venv/bin/activate`
3.  **Install Dependencies:** `pip install -r requirements.txt`

### Running the Application
- **Start Development Server:** `python app.py`
- **Default URL:** `http://127.0.0.1:5001`

### Testing
- **Run All Tests:** `pytest`

## Development Conventions

### Coding Style
- **Python:** Adhere to **PEP 8**. Use snake_case for functions and variables.
- **HTML/CSS:** Follow the established "Step X" comment pattern for educational tracking.
- **Type Hints:** Use Python type hints for improved clarity and tooling support.

### Frontend Conventions
- **Template Inheritance:** All new templates **must** extend `templates/base.html`.
- **Styling:** Use CSS variables defined in `:root` in `static/css/style.css` for consistent colors and spacing.
- **Modularity:** Keep page-specific logic separated in `app.py` and dedicated CSS files where appropriate.

### Database Guidelines
- **SQLite Configuration:** Always ensure `PRAGMA foreign_keys = ON;` is executed for every database connection to maintain referential integrity.
- **Schema Management:** Keep all table creation logic within `database/db.py`.

## Educational Context
This project is structured as a guided learning experience. 
- **Placeholders:** Routes and functions marked with "coming in Step X" indicate pending implementation tasks.
- **Progress Tracking:** Do not remove the "Step X" comments as they are used to track the curriculum progress.

## Subagent Policy
- Always use a builtin explore subagent for codebase exploration 
  before implementing any new feature
- Always use a subagent to verify test results 
  after any implementation
- When asked to plan, delegate codebase research 
  to a subagent before presenting the plan
- always use a builtin plan subagent in plan mode


## Commands
```bash
# Setup
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run dev server (port 5001)
python app.py

# Run all tests
pytest

# Run a specific test file
pytest tests/test_foo.py

# Run a specific test by name
pytest -k "test_name"

# Run tests with output visible
pytest -s
```

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this
