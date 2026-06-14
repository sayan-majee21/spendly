# Implementation Plan: Login and Logout (Step 3)

## Objective
Implement secure user authentication as defined in `03-login-and-logout.md` (v2). This involves creating a database helper to fetch users, updating the Flask routes to handle session state, and modifying the Jinja templates to conditionally display navigation links based on authentication status.

## Phase 1: Database Layer (`database/db.py`)
**Goal:** Provide a secure, isolated way for the application routing logic to retrieve user data by email.

1.  **Add `get_user_by_email(email)` function:**
    *   **Connection:** Obtain a database connection using the existing `get_db()` helper.
    *   **Query:** Execute a parameterized `SELECT * FROM users WHERE email = ?` query to prevent SQL injection.
    *   **Execution:** Use `cursor.fetchone()` to retrieve the user record.
    *   **Return:** Return the resulting `sqlite3.Row` object. If no user is found, this will naturally return `None`.
    *   **Cleanup:** Ensure the database connection is closed properly (e.g., using a `finally` block or context manager).

## Phase 2: Application Routing & Session Management (`app.py`)
**Goal:** Handle the authentication workflow, including credential verification, session management, and user feedback.

1.  **Dependencies:**
    *   Import `check_password_hash` from `werkzeug.security`.
    *   Import `session` from `flask`.
    *   Import `get_user_by_email` from `database.db`.

2.  **Update `/register` and `/login` Routes:**
    *   **Auth Check:** If `session.get("user_id")` exists, redirect to `url_for("landing")`.
    *   Modify `/login` decorator to accept `methods=["GET", "POST"]`.
    *   **GET Request:** Continue to render `login.html`.
    *   **POST Request Workflow:**
        *   Extract `email` and `password` from `request.form`.
        *   Call `get_user_by_email(email)`.
        *   **Validation:** 
            *   If the user exists AND `check_password_hash(user['password_hash'], password)` is `True`:
                *   Set `session["user_id"] = user["id"]`.
                *   Set `session["user_name"] = user["name"]`.
                *   Use `flash()` to display a success message (e.g., "Welcome back, [Name]!").
                *   Return a redirect to `url_for("landing")`.
            *   If the user does not exist OR the password check fails:
                *   Use `flash()` to display a generic error message: "Invalid email or password." (Do not reveal whether the email or password was wrong for security reasons).
                *   Render the `login.html` template so the user can try again.

3.  **Update `/logout` Route:**
    *   Call `session.clear()` to completely wipe the current session data.
    *   Use `flash()` to display a success message: "Logged out successfully."
    *   Return a redirect to `url_for("landing")`.

## Phase 3: Template Adjustments (`templates/`)
**Goal:** Reflect the user's authentication state in the UI and integrate with the global flash message system.

1.  **Update `login.html`:**
    *   Remove the explicit `{% if error %}` block, as errors are now handled by the global flashed messages in `base.html`.
    *   Ensure the `<form>` tag explicitly defines `method="POST"` and `action="{{ url_for('login') }}"`.

2.  **Update `base.html`:**
    *   Locate the `<div class="nav-links">` section.
    *   Introduce a Jinja conditional: `{% if session.get('user_id') %}`.
    *   **True (Authenticated):** Display links to the Profile (`url_for('profile')`) and Sign Out (`url_for('logout')`).
    *   **False (Guest):** Display links to Sign In (`url_for('login')`) and Get Started (`url_for('register')`).

## Phase 4: Verification (Definition of Done)
*   **Manual Testing:**
    *   Attempt login with non-existent email -> Verify generic error flash.
    *   Attempt login with correct email but wrong password -> Verify generic error flash.
    *   Attempt login with correct credentials -> Verify redirect to `/` (landing) and success flash.
    *   Verify navigation bar changes to "Profile" and "Sign out" upon successful login.
    *   Click "Sign out" -> Verify redirect to landing page, success flash, and navigation bar reverts to "Sign in" and "Get started".
*   **Code Review:** Ensure no raw passwords are being checked or stored in the session, and that the "Step X" educational comment markers remain intact.
