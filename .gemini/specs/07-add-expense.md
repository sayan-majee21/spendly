# Spec: Add Expense

## Overview
Step 7 implements the **Add Expense** flow, giving authenticated users a form to
record a new expense. The existing stub route `GET /expenses/add` is upgraded to
handle both `GET` (render the empty form) and `POST` (validate and persist the
new record). On success the user is redirected to `/profile` with a flash
confirmation. On validation failure the form is re-rendered with the user's
input preserved and an error flash message.

## Depends on
- Step 1: Database setup (`expenses` table must exist with columns `user_id`,
  `amount`, `category`, `date`, `description`)
- Step 3: Login / logout (session must store `user_id`; route must be
  login-protected)
- Step 5/6: `get_db()` helper in `database/db.py` already enforces
  `PRAGMA foreign_keys = ON`

## Routes

| Method | Path            | Auth required | Description                              |
|--------|-----------------|---------------|------------------------------------------|
| GET    | `/expenses/add` | Yes           | Render the blank add-expense form        |
| POST   | `/expenses/add` | Yes           | Validate form data, insert row, redirect |

Both methods share the same route function `add_expense()`.

### GET behaviour
- If the user is not logged in → redirect to `/login` with flash error
  `"Please log in to add an expense."`
- Otherwise render `templates/add_expense.html` with an empty form

### POST behaviour
1. Require login; redirect unauthenticated requests to `/login`
2. Read form fields: `amount`, `category`, `date`, `description`
3. **Validate** (server-side):
   - `amount`: required; must be a positive float; maximum value `999_999.99`
   - `category`: required; must be one of the eight allowed values (see below)
   - `date`: required; must parse as `YYYY-MM-DD`; must not be in the future
   - `description`: optional; if provided, strip whitespace; max 200 characters
4. If any validation fails → flash an error message, re-render the form with
   the submitted values preserved (pass them back to the template)
5. If all validations pass → call `db_add_expense()` in `database/db.py`
6. On success → `flash("Expense added successfully.", "success")` then
   `redirect(url_for("profile"))`

### Allowed categories (exact strings, enforced server-side)
```
Food, Transport, Bills, Health, Entertainment, Shopping, Education, Other
```

## Database changes

### New function: `add_expense()` in `database/db.py`

```python
def add_expense(user_id: int, amount: float, category: str,
                date: str, description: str | None) -> bool:
    """
    Inserts a new expense row for the given user.
    Returns True on success, False on any database error.
    """
```

- Uses `get_db()` (FK enforcement already set)
- Parameterised `INSERT INTO expenses (user_id, amount, category, date,
  description) VALUES (?, ?, ?, ?, ?)`
- Returns `True` on `conn.commit()`, `False` on `Exception`
- Always closes the connection in a `finally` block

No schema changes — the `expenses` table defined in Step 1 already contains all
required columns.

## Templates

### New: `templates/add_expense.html`
- Extends `base.html`
- Contains a single `<form method="POST" action="{{ url_for('add_expense') }}">`
- **Fields**:

| Field       | Element                               | Notes                                                        |
|-------------|---------------------------------------|--------------------------------------------------------------|
| Amount (Rs) | `<input type="number" name="amount">` | `step="0.01"`, `min="0.01"`, `max="999999.99"`, required    |
| Category    | `<select name="category">`            | Eight `<option>` values; pre-select submitted value on re-render |
| Date        | `<input type="date" name="date">`     | `max` attribute set to today via Jinja; required             |
| Description | `<textarea name="description">`       | Optional; `maxlength="200"`; 3 rows                          |
| Submit      | `<button type="submit">`              | Label: "Add Expense"                                         |

- A visible "Back to Profile" link pointing to `url_for("profile")`
- Flash messages rendered at the top of the form (reuse pattern from existing templates)
- Must include `{% block scripts %}{% endblock %}` even if empty

### Modified: `templates/profile.html`
- Add an "Add Expense" button/link (rendered as a styled `<a>` tag) somewhere
  visible in the header or stats area, pointing to `url_for("add_expense")`
- No other structural changes

## Files to change

| File | Change |
|------|--------|
| `app.py` | Upgrade `add_expense()` stub: accept `GET`/`POST`, add login guard, validation logic, call `db_add_expense()`, flash + redirect |
| `database/db.py` | Add `add_expense(user_id, amount, category, date, description) -> bool` |
| `templates/profile.html` | Add "Add Expense" CTA link |

## Files to create

| File | Purpose |
|------|---------|
| `templates/add_expense.html` | Add-expense form page |
| `static/css/add_expense.css` | Page-specific styles for the form |

## New dependencies
None. No new packages required.

## Rules for implementation
- The route function signature must use a type hint:
  `def add_expense() -> Union[str, Response]:`
- Import `add_expense` from `database.db` and alias it to avoid collision with
  the Flask view function:
  `from database.db import add_expense as db_add_expense`
- Never string-format user input into SQL — parameterised queries only
- Never hardcode hex colours — use CSS variables from `style.css`
- All templates must extend `base.html`
- No inline styles
- The `date` field `max` value must be set to today's date in `YYYY-MM-DD`
  format, computed in `app.py` and passed to the template as `today`
- Amount validation must use `float()` inside a `try/except ValueError`; never
  trust the browser's `<input type="number">` alone
- Category must be validated against an explicit allowlist in `app.py`, not just
  trusted from the `<select>` element
- `description` is optional: if the field is empty or whitespace-only, store
  `None` (not an empty string) in the database
- Use the POST/Redirect/GET pattern after a successful insert to prevent
  duplicate submissions on browser refresh

## Definition of done
- [ ] `GET /expenses/add` renders the form for a logged-in user
- [ ] `GET /expenses/add` redirects unauthenticated users to `/login` with a
  flash error
- [ ] Submitting the form with all valid fields inserts one row into `expenses`
  and redirects to `/profile`
- [ ] A flash message `"Expense added successfully."` is visible after the redirect
- [ ] The new expense appears in the transactions list on `/profile`
- [ ] Submitting with a missing `amount` re-renders the form with an error flash
- [ ] Submitting with a non-numeric `amount` (e.g. `"abc"`) re-renders the form
  with an error flash
- [ ] Submitting with a negative or zero `amount` re-renders the form with an
  error flash
- [ ] Submitting with a future date re-renders the form with an error flash
- [ ] Submitting with an invalid category string (tampered POST) re-renders the
  form with an error flash
- [ ] Submitting with an empty description stores `NULL` in the database (not
  an empty string)
- [ ] Submitting with a description longer than 200 characters re-renders with
  an error flash
- [ ] The profile page has a visible "Add Expense" link pointing to
  `/expenses/add`
- [ ] All form fields retain their submitted values when the form is re-rendered
  after a validation error
- [ ] `static/css/add_expense.css` uses only CSS variables for colours
