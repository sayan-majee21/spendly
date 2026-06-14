# Spec: Registration (v2)

## Overview
This feature implements the core user registration flow. It enables new users to create an account by providing their full name, email address, and a password. This is a foundational step for all authenticated features in Spendly. The implementation will focus on security and user experience by properly hashing passwords, providing clear error feedback, and preventing duplicate accounts. ON successful registration, show a success message and redirect to login page

## Depends on
- Step 1: Database Setup

## Routes
The existing `/register` route will be updated to handle both `GET` and `POST` requests.
- `GET /register`: Renders the registration page (`register.html`). No changes to the existing render logic.
- `POST /register`: Handles the form submission. It will validate the user's input, check for an existing email in the database, create the new user record if validation passes, and then redirect.

## Database changes
No schema changes are required. The `users` table is already defined in `database/db.py`.

A new helper function will be added to `database/db.py` to encapsulate user creation logic, following our separation of concerns principle.
- **`create_user(name, email, password)`**: This function will:
    1.  Take `name`, `email`, and `password` as arguments.
    2.  Hash the raw password using `werkzeug.security.generate_password_hash`.
    3.  Execute a parameterized `INSERT` statement to add the new user to the `users` table.
    4.  Wrap the database call in a `try...except sqlite3.IntegrityError` block to gracefully handle duplicate email addresses.
    5.  Return a boolean or the user object on success, and `None` or `False` on failure (e.g., duplicate email).

## Templates
- **Modify:** `templates/base.html`
  - Add a dedicated section to render flashed messages using `get_flashed_messages(with_categories=true)`. This will allow all pages that extend `base.html` to display alerts for errors, successes, and information. The messages should be styled to be noticeable but not disruptive.

- **Modify:** `templates/register.html`
  - The existing form structure is sufficient.
  - The explicit `{% if error %}` block will be removed in favor of the global flashed message system being added to `base.html`.

## Files to change
- `app.py`:
    - Update the `register()` route to accept `methods=['GET', 'POST']`.
    - Implement the `POST` logic:
        - Retrieve `name`, `email`, and `password` from the form.
        - Perform basic validation (check for empty fields).
        - Call the new `create_user()` function from `database/db.py`.
        - Use `flash()` to provide feedback (e.g., "Registration successful! Please log in." or "Email already in use.").
        - Redirect to `url_for('login')` on success.
        - Re-render the template on failure.
- `database/db.py`:
    - Add the new `create_user()` helper function as described above.
- `templates/base.html`:
    - Add the flashed messages rendering block, likely just before the `{% block content %}`.

## Files to create
- None.

## New dependencies
- No new dependencies.

## Rules for implementation
- **Separation of Concerns:** All database interaction logic MUST reside in `database/db.py`. The `register()` route in `app.py` should be clean and focused on request handling and control flow.
- **Security:** Passwords MUST be hashed using `werkzeug.security.generate_password_hash`. Raw passwords should never be logged or stored.
- **User Feedback:** Use Flask's `flash()` mechanism for all user-facing messages. Provide clear, helpful messages for both success and error conditions.
- **Input Validation:** The `register` route must validate that `name`, `email`, and `password` are present and not empty strings.
- **Idempotency:** The `create_user` function should fail gracefully if a user with the same email already exists, preventing duplicate records.
- **Redirects:** Always use `url_for()` for redirects to avoid hardcoding URLs.

## Definition of Done
- [ ] Navigating to `/register` displays the registration form.
- [ ] Submitting the form with valid and unique user details creates a new record in the `users` table.
- [ ] The `password_hash` column for the new user is a non-plaintext, hashed string.
- [ ] Submitting the form with an email that already exists in the database does NOT create a new user.
- [ ] Submitting a pre-existing email flashes an appropriate error message (e.g., "Email already registered.") on the registration page.
- [ ] Submitting the form with any of the required fields left empty flashes an error message.
- [ ] After a successful registration, the user is redirected to the `/login` page.
- [ ] A success message is flashed to be displayed on the login page after the redirect.
