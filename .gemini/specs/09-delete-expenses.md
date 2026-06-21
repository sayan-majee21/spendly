# Spec: Delete Expenses

## Overview
Step 9 implements the **Delete Expenses** flow, allowing authenticated users to delete an existing expense they own. The existing stub route `GET /expenses/<int:id>/delete` is upgraded to perform authorization checks, delete the expense from the database, and redirect the user back to the profile page.

## Depends on
- Step 1: Database setup (`expenses` table must exist with columns `id`, `user_id`, `amount`, `category`, `date`, `description`)
- Step 3: Login / logout (session must store `user_id`; route must be login-protected)
- Step 5/6: `get_db()` helper in `database/db.py` already enforces `PRAGMA foreign_keys = ON`
- Step 7/8: Expenses are populated and can be edited/viewed

## Routes

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| GET | `/expenses/<int:id>/delete` | Yes | Verify ownership, delete the expense with ID `id`, and redirect to `/profile` |

### GET behaviour
1. If the user is not logged in → redirect to `/login` with flash error `"Please log in to delete an expense."`
2. Fetch the expense record from the database using the provided `id`.
   - If the expense does not exist → redirect to `/profile` with flash error `"Expense not found."`
   - If the expense does not belong to the logged-in user (`expense["user_id"] != session["user_id"]`) → redirect to `/profile` with flash error `"You are not authorized to delete this expense."`
3. If ownership and existence checks pass, call `delete_expense(id)` in `database/db.py`.
4. If deletion is successful:
   - Flash a success message: `"Expense deleted successfully."`
   - Redirect to `/profile` (using `redirect(url_for("profile"))`)
5. If deletion fails (database error/IntegrityError):
   - Flash an error message: `"Something went wrong. Please try again."`
   - Redirect to `/profile`

## Database changes

### New functions in `database/db.py`

#### `delete_expense(expense_id: int) -> bool`
```python
def delete_expense(expense_id: int) -> bool:
    """
    Deletes the specified expense row from the database.
    Returns True on success, False on error.
    """
```
- Parameterised query: `DELETE FROM expenses WHERE id = ?`

No schema changes required.

## Templates & Styling

### Modified: `templates/profile.html`
- Modify the transactions table's action column to include a "Delete" link next to the "Edit" link:
  ```html
  <a href="{{ url_for('delete_expense', id=tx.id) }}" class="btn-delete" onclick="return confirm('Are you sure you want to delete this expense?');">Delete</a>
  ```
- Ensure the delete action includes a browser confirmation dialog (`onclick="return confirm(...);"`) to prevent accidental clicks from triggering immediate deletion.

### Modified: `static/css/profile.css`
- Add styling for the delete button (`.btn-delete`) to align with the "Paper & Ink" design conventions, using `--danger` for its text color and background on hover:
  ```css
  .btn-delete {
      display: inline-block;
      padding: 0.35rem 0.75rem;
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--danger);
      background: transparent;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      text-decoration: none;
      transition: all 0.2s ease;
      margin-left: 0.5rem;
  }

  .btn-delete:hover {
      border-color: var(--danger);
      color: var(--paper);
      background: var(--danger);
  }
  ```

## Files to change

| File | Change |
|------|--------|
| `app.py` | 1. Import `delete_expense` from `database.db`. <br>2. Upgrade `delete_expense(id)` route to implement authentication, ownership validation, delete execution, and redirection with proper flash messages. |
| `database/db.py` | Add `delete_expense(expense_id: int) -> bool`. |
| `templates/profile.html` | Add "Delete" link next to the "Edit" link in the Actions column of the transactions table. |
| `static/css/profile.css` | Add styling for `.btn-delete`. |

## Files to create
None.

## New dependencies
None.

## Rules for implementation
- The route function signature must use type hints:
  `def delete_expense(id: int) -> Union[str, Response]:`
- Import `delete_expense` from `database.db`.
- Never string-format user input into SQL — parameterised queries only.
- Never hardcode colors — use CSS variables like `var(--danger)` from `style.css`.
- Ensure confirmation dialog exists on the delete link to protect the user from accidental action.

## Definition of done
- [ ] Clicking the "Delete" link on the profile page triggers a browser confirmation dialog.
- [ ] Canceling the confirmation dialog prevents the deletion request.
- [ ] Confirming the deletion redirects to `/profile` and successfully deletes the expense from the database.
- [ ] A success flash message `"Expense deleted successfully."` is visible on `/profile` after deletion redirect.
- [ ] The deleted expense is no longer visible in the transaction table or reflected in the user stats / category breakdown.
- [ ] Attempting to delete an expense while unauthenticated redirects to `/login` with flash error `"Please log in to delete an expense."`.
- [ ] Attempting to delete a nonexistent expense redirects to `/profile` with flash error `"Expense not found."`.
- [ ] Attempting to delete another user's expense redirects to `/profile` with flash error `"You are not authorized to delete this expense."`.
- [ ] Database helper `delete_expense` closes the connection cleanly in a `finally` block.
- [ ] All tests in `tests/test_09-delete-expenses.py` pass cleanly.
