# Spendly Coding Standards

These rules apply to all code in the Spendly repository.

## Python (Flask)
- Use **Type Hints** for all route functions.
- Follow **PEP 8** strictly.
- Database connections must be closed properly using a context manager or `teardown_appcontext`.

## HTML/CSS
- Use CSS variables for all colors.
- Ensure all pages are responsive (check the `@media` queries in `style.css`).
- Every template must include a `{% block scripts %}` even if empty.

## Git
- Branch names should be descriptive (e.g., `feature/add-expense`).
- Commit messages must follow the "feat:", "fix:", or "docs:" prefix convention.
