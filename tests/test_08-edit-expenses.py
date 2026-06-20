import pytest
from datetime import date, timedelta
from unittest.mock import patch
from database.db import get_db, create_user

# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_client(client, app):
    """A test client that is already logged in as a freshly-created test user."""
    with app.app_context():
        create_user("Test User", "test@example.com", "password123")

    client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True,
    )
    return client


def _get_test_user_id():
    """Return the DB id of the standard test user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"]


def _today() -> str:
    """Return today's date as an ISO string (YYYY-MM-DD)."""
    return date.today().isoformat()


def _future_date() -> str:
    """Return tomorrow's date as an ISO string."""
    return (date.today() + timedelta(days=1)).isoformat()


def _valid_form(**overrides) -> dict:
    """Return a dict of valid POST fields; individual fields can be overridden."""
    data = {
        "amount": "50.00",
        "category": "Food",
        "date": _today(),
        "description": "Updated test lunch",
    }
    data.update(overrides)
    return data


def _insert_test_expense(user_id: int, amount: float, category: str, date_str: str, description: str) -> int:
    """Inserts a test expense for the user and returns the inserted ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date_str, description)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id

# ---------------------------------------------------------------------------
# GET /expenses/<id>/edit
# ---------------------------------------------------------------------------

class TestGetEditExpense:

    def test_get_edit_unauthenticated_redirects(self, client):
        """GET /expenses/1/edit redirects to /login for unlogged users."""
        response = client.get("/expenses/1/edit")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_get_edit_unauthenticated_flashes_error(self, client):
        """GET /expenses/1/edit flashes correct error message for unlogged users."""
        response = client.get("/expenses/1/edit", follow_redirects=True)
        assert b"Please log in to edit an expense." in response.data

    def test_get_edit_nonexistent_redirects(self, auth_client):
        """GET /expenses/9999/edit redirects to /profile if expense does not exist."""
        response = auth_client.get("/expenses/9999/edit")
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_get_edit_nonexistent_flashes_error(self, auth_client):
        """GET /expenses/9999/edit flashes 'Expense not found.' error."""
        response = auth_client.get("/expenses/9999/edit", follow_redirects=True)
        assert b"Expense not found." in response.data

    def test_get_edit_unauthorized_redirects(self, auth_client, app):
        """GET /expenses/<id>/edit redirects to /profile if expense belongs to another user."""
        with app.app_context():
            # Create another user and insert an expense for them
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", _today(), "Other user's bill")

        response = auth_client.get(f"/expenses/{other_expense_id}/edit")
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_get_edit_unauthorized_flashes_error(self, auth_client, app):
        """GET /expenses/<id>/edit flashes 'You are not authorized to edit this expense.'."""
        with app.app_context():
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", _today(), "Other user's bill")

        response = auth_client.get(f"/expenses/{other_expense_id}/edit", follow_redirects=True)
        assert b"You are not authorized to edit this expense." in response.data

    def test_get_edit_prepopulated_returns_200(self, auth_client, app):
        """GET /expenses/<id>/edit renders the edit page pre-populated for the authenticated owner."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 42.50, "Food", "2026-06-15", "Original description")

        response = auth_client.get(f"/expenses/{expense_id}/edit")
        assert response.status_code == 200
        assert b"Edit Expense" in response.data
        assert b'name="amount"' in response.data
        assert b"42.5" in response.data
        assert b"Original description" in response.data
        assert b"2026-06-15" in response.data
        assert b"Food" in response.data

# ---------------------------------------------------------------------------
# POST /expenses/<id>/edit -- happy path and basic tests
# ---------------------------------------------------------------------------

class TestPostEditExpense:

    def test_post_edit_unauthenticated_redirects(self, client):
        """POST /expenses/1/edit redirects to /login for unlogged users."""
        response = client.post("/expenses/1/edit", data=_valid_form())
        assert response.status_code == 302
        assert "/login" in response.location

    def test_post_edit_unauthenticated_flashes_error(self, client):
        """POST /expenses/1/edit flashes correct error message for unlogged users."""
        response = client.post("/expenses/1/edit", data=_valid_form(), follow_redirects=True)
        assert b"Please log in to edit an expense." in response.data

    def test_post_edit_nonexistent_redirects(self, auth_client):
        """POST /expenses/9999/edit redirects to /profile if expense does not exist."""
        response = auth_client.post("/expenses/9999/edit", data=_valid_form())
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_post_edit_nonexistent_flashes_error(self, auth_client):
        """POST /expenses/9999/edit flashes 'Expense not found.' error."""
        response = auth_client.post("/expenses/9999/edit", data=_valid_form(), follow_redirects=True)
        assert b"Expense not found." in response.data

    def test_post_edit_unauthorized_redirects(self, auth_client, app):
        """POST /expenses/<id>/edit redirects to /profile if expense belongs to another user."""
        with app.app_context():
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", _today(), "Other user's bill")

        response = auth_client.post(f"/expenses/{other_expense_id}/edit", data=_valid_form())
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_post_edit_unauthorized_flashes_error(self, auth_client, app):
        """POST /expenses/<id>/edit flashes 'You are not authorized to edit this expense.'."""
        with app.app_context():
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", _today(), "Other user's bill")

        response = auth_client.post(f"/expenses/{other_expense_id}/edit", data=_valid_form(), follow_redirects=True)
        assert b"You are not authorized to edit this expense." in response.data

    def test_post_edit_success_updates_db(self, auth_client, app):
        """Valid POST updates the expense details in the database."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="15.50", category="Bills", date="2026-06-12", description="New bill")
        )
        assert response.status_code == 302
        assert "/profile" in response.location

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            conn.close()

        assert row is not None
        assert row["amount"] == 15.50
        assert row["category"] == "Bills"
        assert row["date"] == "2026-06-12"
        assert row["description"] == "New bill"

    def test_post_edit_success_flashes_message(self, auth_client, app):
        """Valid POST shows 'Expense updated successfully.' flash message."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="15.50"),
            follow_redirects=True
        )
        assert b"Expense updated successfully." in response.data

    def test_post_edit_success_reflected_on_profile(self, auth_client, app):
        """Valid POST changes are rendered in the profile transaction list."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="15.50", category="Bills", date="2026-06-12", description="New bill"),
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"15.50" in response.data or b"15,50" in response.data or b"15" in response.data
        assert b"Bills" in response.data
        assert b"2026-06-12" in response.data
        assert b"New bill" in response.data

    def test_post_edit_db_failure_flashes_error(self, auth_client, app):
        """On update_expense returning False, flash error and re-render the form."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        with patch("app.update_expense", return_value=False):
            response = auth_client.post(
                f"/expenses/{expense_id}/edit",
                data=_valid_form(amount="15.50", category="Bills"),
                follow_redirects=True
            )
            assert response.status_code == 200
            assert b"Something went wrong" in response.data

# ---------------------------------------------------------------------------
# POST /expenses/<id>/edit -- validation failures & field preservation
# ---------------------------------------------------------------------------

class TestPostEditExpenseValidation:

    def test_missing_amount_rerenders_form_with_error(self, auth_client, app):
        """POST with empty amount re-renders form with validation error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_non_numeric_amount_rerenders_form_with_error(self, auth_client, app):
        """POST with non-numeric amount ('abc') re-renders form with validation error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="abc")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_zero_amount_rerenders_form_with_error(self, auth_client, app):
        """POST with zero amount re-renders form with validation error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="0")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_too_large_amount_rerenders_form_with_error(self, auth_client, app):
        """POST with amount > 999999.99 re-renders form with validation error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="1000000.00")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_negative_amount_error(self, auth_client, app):
        """POST with negative amount re-renders form with error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="-5.00")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_future_date_error(self, auth_client, app):
        """POST with future date re-renders form with error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(date=_future_date())
        )
        assert response.status_code == 200
        assert b"future" in response.data or b"date" in response.data

    def test_invalid_date_format_error(self, auth_client, app):
        """POST with malformed date format (e.g. "not-a-date") re-renders form with error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(date="not-a-date")
        )
        assert response.status_code == 200
        assert b"date" in response.data or b"Please enter" in response.data

    def test_invalid_category_error(self, auth_client, app):
        """POST with invalid category string re-renders form with error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(category="HackerCategory")
        )
        assert response.status_code == 200
        assert b"category" in response.data or b"Please select" in response.data

    def test_description_too_long_error(self, auth_client, app):
        """POST with description longer than 200 characters re-renders form with error."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(description="A" * 201)
        )
        assert response.status_code == 200
        assert b"200" in response.data or b"characters" in response.data

    def test_form_preserves_amount_on_validation_error(self, auth_client, app):
        """After a validation error, the submitted amount is preserved in the re-rendered form."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="12.34", category="HackerCategory"),
        )
        assert response.status_code == 200
        assert b"12.34" in response.data

    def test_form_preserves_category_on_validation_error(self, auth_client, app):
        """After a validation error, the submitted category is preserved in the re-rendered form."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="-5.00", category="Shopping"),
        )
        assert response.status_code == 200
        assert b"Shopping" in response.data

    def test_form_preserves_date_on_validation_error(self, auth_client, app):
        """After a validation error, the submitted date is preserved in the re-rendered form."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="-5.00", date="2026-01-15"),
        )
        assert response.status_code == 200
        assert b"2026-01-15" in response.data

    def test_form_preserves_description_on_validation_error(self, auth_client, app):
        """After a validation error, the submitted description is preserved in the re-rendered form."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        response = auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(amount="-5.00", description="Preserve my text"),
        )
        assert response.status_code == 200
        assert b"Preserve my text" in response.data

# ---------------------------------------------------------------------------
# POST /expenses/<id>/edit -- empty description stored as NULL
# ---------------------------------------------------------------------------

class TestPostEditExpenseNullDescription:

    def test_empty_description_stored_as_null(self, auth_client, app):
        """POST with empty description stores NULL (not empty string) in the DB."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(description=""),
        )

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT description FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            conn.close()

        assert row is not None
        assert row["description"] is None

    def test_whitespace_only_description_stored_as_null(self, auth_client, app):
        """POST with whitespace-only description stores NULL in the DB."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 10.00, "Transport", "2026-06-10", "Bus ride")

        auth_client.post(
            f"/expenses/{expense_id}/edit",
            data=_valid_form(description="   "),
        )

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT description FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            conn.close()

        assert row is not None
        assert row["description"] is None

# ---------------------------------------------------------------------------
# Profile page Edit link
# ---------------------------------------------------------------------------

class TestProfileEditExpenseLink:

    def test_profile_contains_link_to_edit_expense(self, auth_client, app):
        """The /profile page contains a link pointing to the edit route for each expense."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 25.00, "Food", _today(), "My lunch")

        response = auth_client.get("/profile")
        assert response.status_code == 200
        assert f"/expenses/{expense_id}/edit".encode() in response.data
