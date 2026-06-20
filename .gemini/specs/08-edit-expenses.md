# Spec: Edit Expenses

## Overview
Step 8 implements the **Edit Expenses** flow, allowing authenticated users to modify details of an existing expense. The existing stub route `GET /expenses/<int:id>/edit` is upgraded to support both `GET` (fetch and display the current state of a specific expense in a form) and `POST` (validate and update the database record). On success, the user is redirected to `/profile` with a success flash message. On validation failure, the edit form is re-rendered with the user's input preserved and an error flash message. Access control checks are implemented to ensure that a user can only view/edit their own expenses.

## Depends on
- Step 1: Database setup (`expenses` table must exist with columns `id`, `user_id`, `amount`, `category`, `date`, `description`)
- Step 3: Login / logout (session must store `user_id`; route must be login-protected)
- Step 5/6: `get_db()` helper in `database/db.py` already enforces `PRAGMA foreign_keys = ON`
- Step 7: Add Expense (defines validation rules for expense fields)

## Routes

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| GET | `/expenses/<int:id>/edit` | Yes | Fetch and render the edit-expense form pre-populated with details of the expense having ID `id` |
| POST | `/expenses/<int:id>/edit` | Yes | Validate form data, update expense row, redirect |

Both methods share the same route function `edit_expense(id: int)`.

### GET behaviour
- If the user is not logged in → redirect to `/login` with flash error `"Please log in to edit an expense."`
- Fetch the expense record from the database using the provided `id`.
  - If the expense does not exist → redirect to `/profile` with flash error `"Expense not found."`
  - If the expense does not belong to the logged-in user (`expense["user_id"] != session["user_id"]`) → redirect to `/profile` with flash error `"You are not authorized to edit this expense."`
- Otherwise, render `templates/edit_expense.html` pre-populated with the expense details.

### POST behaviour
1. Require login; redirect unauthenticated requests to `/login`
2. Fetch the expense record from the database using the provided `id`.
  - If the expense does not exist → redirect to `/profile` with flash error `"Expense not found."`
  - If the expense does not belong to the logged-in user → redirect to `/profile` with flash error `"You are not authorized to edit this expense."`
3. Read form fields: `amount`, `category`, `date`, `description`
4. **Validate** (server-side, identical to Step 7):
   - `amount`: required; must be a positive float; value must be between `0.01` and `999999.99`
   - `category`: required; must be one of the eight allowed values (see below)
   - `date`: required; must parse as `YYYY-MM-DD`; must not be in the future
   - `description`: optional; if provided, strip whitespace; max 200 characters
5. If any validation fails → flash the validation error message, and re-render the form with the submitted values preserved (pass them back to the template as `form`).
6. If all validations pass → call `update_expense(expense_id, amount, category, date_str, description)` in `database/db.py`.
7. On success → `flash("Expense updated successfully.", "success")` then `redirect(url_for("profile"))`.
8. On failure/exception → `flash("Something went wrong. Please try again.", "error")` then re-render `templates/edit_expense.html`.

### Allowed categories (exact strings, enforced server-side)
```
Food, Transport, Bills, Health, Entertainment, Shopping, Education, Other
```

## Database changes

### New functions in `database/db.py`

#### `get_expense_by_id(expense_id: int) -> Optional[sqlite3.Row]`
```python
def get_expense_by_id(expense_id: int) -> Optional[sqlite3.Row]:
    """
    Retrieves a single expense by its ID.
    Returns the sqlite3.Row if found, or None otherwise.
    """
```
- Parameterised query: `SELECT * FROM expenses WHERE id = ?`

#### `update_expense(expense_id: int, amount: float, category: str, date_str: str, description: Optional[str]) -> bool`
```python
def update_expense(expense_id: int, amount: float, category: str,
                   date_str: str, description: Optional[str]) -> bool:
    """
    Updates the specified expense row in the database.
    Returns True on success, False on IntegrityError or error.
    """
```
- Parameterised query: `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?`

No schema changes required.

## Templates

### New: `templates/edit_expense.html`
- Extends `base.html`
- Contains a single `<form method="POST" action="{{ url_for('edit_expense', id=expense.id) }}">` (or matching form action)
- **Fields**:

| Field | Element | Notes |
|-------|---------|-------|
| Amount (Rs) | `<input type="number" name="amount">` | `step="0.01"`, `min="0.01"`, `max="999999.99"`, pre-populated, required |
| Category | `<select name="category">` | Eight `<option>` values; pre-select existing/submitted value on render/re-render |
| Date | `<input type="date" name="date">` | `max` attribute set to today via Jinja; pre-populated, required |
| Description | `<textarea name="description">` | Optional; `maxlength="200"`; 3 rows; pre-populated |
| Submit | `<button type="submit">` | Label: "Save Changes" |

- A visible "Cancel" / "Back to Profile" link pointing to `url_for("profile")`
- Flash messages rendered at the top of the form (reuse pattern from existing templates)
- Must include `{% block scripts %}{% endblock %}` even if empty

### Modified: `templates/profile.html`
- Modify the transactions table to add an "Actions" column (header and body row)
- Include an "Edit" link for each transaction row:
  ```html
  <a href="{{ url_for('edit_expense', id=tx.id) }}" class="btn-edit">Edit</a>
  ```
  *(Note: No Delete link is added yet, as that belongs to Step 9).*

## Files to change

| File | Change |
|------|--------|
| `app.py` | 1. Include `id` in the dict items of `transactions` list returned by `profile()`: `"id": exp["id"]`. <br>2. Upgrade `edit_expense(id)` stub to handle GET/POST, enforce authentication, perform ownership access control, validate fields, and update the database row. |
| `database/db.py` | Add `get_expense_by_id(expense_id: int) -> Optional[sqlite3.Row]` and `update_expense(expense_id: int, amount: float, category: str, date_str: str, description: Optional[str]) -> bool`. |
| `templates/profile.html` | Add "Actions" column to the transactions table and insert the "Edit" link. |

## Files to create

| File | Purpose |
|------|---------|
| `templates/edit_expense.html` | Edit-expense form page |
| `static/css/edit_expense.css` | Page-specific styles for the edit form |

## New dependencies
None.

## Rules for implementation
- The route function signature must use type hints:
  `def edit_expense(id: int) -> Union[str, Response]:`
- Import `get_expense_by_id` and `update_expense` from `database.db`.
- Never string-format user input into SQL — parameterised queries only.
- Never hardcode colors — use CSS variables from `style.css`.
- All templates must extend `base.html`.
- No inline styles.
- The `date` field `max` value must be set to today's date in `YYYY-MM-DD` format, computed in `app.py` and passed to the template.
- Amount validation must use `float()` inside a `try/except ValueError`.
- Category must be validated against `ALLOWED_CATEGORIES` in `app.py`.
- `description` is optional: if the field is empty or whitespace-only, store `None`.
- Use the POST/Redirect/GET pattern after a successful update to prevent duplicate submissions on browser refresh.

## Definition of done
- [ ] `GET /expenses/<id>/edit` renders the edit form for the logged-in owner of the expense.
- [ ] `GET /expenses/<id>/edit` redirects unauthenticated users to `/login` with a flash error.
- [ ] `GET /expenses/<id>/edit` redirects to `/profile` with a flash error if the expense does not exist.
- [ ] `GET /expenses/<id>/edit` redirects to `/profile` with a flash error if the expense belongs to another user.
- [ ] Submitting valid edits updates the corresponding row in the `expenses` table and redirects to `/profile`.
- [ ] A success flash message `"Expense updated successfully."` is visible on `/profile` after redirect.
- [ ] The updated values (amount, date, description, category badge) are reflected on `/profile`.
- [ ] Submitting with a missing `amount` re-renders the edit form with an error flash.
- [ ] Submitting with a non-numeric `amount` (e.g., `"abc"`) re-renders the edit form with an error flash.
- [ ] Submitting with a negative or zero `amount` re-renders the edit form with an error flash.
- [ ] Submitting with a future date re-renders the edit form with an error flash.
- [ ] Submitting with an invalid category string re-renders the edit form with an error flash.
- [ ] Submitting with a description longer than 200 characters re-renders the edit form with an error flash.
- [ ] The transaction list on the profile page has an "Edit" link for each row, linking to `/expenses/<id>/edit`.
- [ ] All form fields retain their submitted values when the form is re-rendered after a validation error.
- [ ] `static/css/edit_expense.css` uses only CSS variables for styling.
