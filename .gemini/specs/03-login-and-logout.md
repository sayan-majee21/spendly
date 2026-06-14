# Spec: Login and Logout (v2)

## Overview
This feature implements secure user authentication. It allows registered users to log in to their accounts and securely log out, ensuring that their session is managed correctly using Flask's `session`. This is a foundational step for personalized expense tracking and profile management.

## Depends on
- **step 01:**Database setup('users' table must be present) 
- **Step 02:** User Registration (requires users to exist in the database and `base.html` to handle flash messages).

## Routes
- `GET /login` — Renders the login form (`login.html`). Redirects to `/` if already logged in. — Public
- `POST /login` — Processes login credentials, verifies password, and starts session. — Public
- `GET /register` — Renders the registration form. Redirects to `/` if already logged in. — Public

## Database changes
No schema changes. We will add a helper to `database/db.py`.

- **`get_user_by_email(email)`**: This function will:
    1.  Take `email` as an argument.
    2.  Execute a parameterized `SELECT *` statement to find the user.
    3.  Return the `sqlite3.Row` (or `None` if not found). This allows `app.py` to access `password_hash`, `id`, and `name`.

## Templates
- **Modify:** `templates/base.html`
  - Update the navigation links inside `<div class="nav-links">`.
  - Use `{% if session.get('user_id') %}` to show "Profile" and "Sign out".
  - Use `{% else %}` to show "Sign in" and "Get started".

- **Modify:** `templates/login.html`
  - Remove the local `{% if error %}` block. All errors should now be handled by the global flash message system in `base.html`.
  - Ensure the form uses `method="POST"` and `action="{{ url_for('login') }}"`.

## Files to change
- `app.py`:
    - Import `check_password_hash` from `werkzeug.security`.
    - Import `session` from `flask`.
    - Update `@app.route("/login")` to handle `GET` and `POST`.
    - In `POST /login`:
        1. Fetch user by email via `get_user_by_email`.
        2. If user exists, verify password with `check_password_hash`.
        3. On success: Set `session["user_id"]` and `session["user_name"]`. Flash success message. Redirect to `/` (landing).
        4. On failure: Flash "Invalid email or password." and re-render login page.
    - Update `@app.route("/logout")`:
        1. `session.clear()`.
        2. Flash "Logged out successfully."
        3. Redirect to `url_for("landing")`.

- `database/db.py`:
    - Add `get_user_by_email(email)` helper function.

- `templates/base.html`:
    - Implement conditional navigation logic.

- `templates/login.html`:
    - Remove redundant error block.

## Rules for implementation
- **Security:** Always use `check_password_hash`. Never compare plain-text passwords.
- **Session Safety:** Use `session.get('user_id')` to check login status.
- **Feedback:** All success/error feedback must use `flash()`.
- **Consistency:** Use `url_for()` for all links and redirects.
- **Educational Markers:** Maintain "Step 3" comment patterns.

## Definition of done
- [ ] Navigating to `/login` shows the sign-in form.
- [ ] Logging in with valid credentials redirects to `/` (landing).
- [ ] Logging in sets `session['user_id']` and `session['user_name']`.
- [ ] Logging in with an incorrect password flashes an "Invalid email or password" error.
- [ ] Logging in with a non-existent email flashes an "Invalid email or password" error.
- [ ] Navigation bar dynamically switches between Guest (Sign in/Get started) and Authenticated (Profile/Sign out) states.
- [ ] Clicking "Sign out" clears the session and redirects to the landing page with a success message.
- [ ] Authenticated users are redirected to `/` when trying to access `/login` or `/register`.
- [ ] All code adheres to the "Step 3" naming conventions and architectural rules.
