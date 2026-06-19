import pytest
from datetime import date, timedelta
from database.db import get_db, create_user


# ---------------------------------------------------------------------------
# Shared fixtures
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
        "description": "Test lunch",
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# GET /expenses/add
# ---------------------------------------------------------------------------

class TestGetAddExpense:

    def test_get_add_expense_authenticated_returns_200(self, auth_client):
        """GET /expenses/add returns 200 for a logged-in user."""
        response = auth_client.get("/expenses/add")
        assert response.status_code == 200

    def test_get_add_expense_contains_amount_field(self, auth_client):
        """GET /expenses/add renders a form with an amount input element."""
        response = auth_client.get("/expenses/add")
        assert b'name="amount"' in response.data

    def test_get_add_expense_contains_category_select(self, auth_client):
        """GET /expenses/add renders a form with a category select element."""
        response = auth_client.get("/expenses/add")
        assert b'name="category"' in response.data

    def test_get_add_expense_contains_date_field(self, auth_client):
        """GET /expenses/add renders a form with a date input element."""
        response = auth_client.get("/expenses/add")
        assert b'name="date"' in response.data

    def test_get_add_expense_contains_description_field(self, auth_client):
        """GET /expenses/add renders a form with a description textarea."""
        response = auth_client.get("/expenses/add")
        assert b'name="description"' in response.data

    def test_get_add_expense_contains_submit_button(self, auth_client):
        """GET /expenses/add renders a submit button labelled Add Expense."""
        response = auth_client.get("/expenses/add")
        assert b"Add Expense" in response.data

    def test_get_add_expense_unauthenticated_redirects_to_login(self, client):
        """GET /expenses/add redirects an unauthenticated user to /login."""
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_get_add_expense_unauthenticated_flashes_error(self, client):
        """GET /expenses/add shows the login-required flash message on the login page."""
        response = client.get("/expenses/add", follow_redirects=True)
        assert b"Please log in to add an expense." in response.data


# ---------------------------------------------------------------------------
# POST /expenses/add -- happy path
# ---------------------------------------------------------------------------

class TestPostAddExpenseSuccess:

    def test_valid_post_inserts_row_in_db(self, auth_client, app):
        """Valid POST inserts exactly one new expense row in the expenses table."""
        with app.app_context():
            user_id = _get_test_user_id()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM expenses WHERE user_id = ?", (user_id,)
            )
            before = cursor.fetchone()["cnt"]
            conn.close()

        auth_client.post("/expenses/add", data=_valid_form())

        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM expenses WHERE user_id = ?",
                (_get_test_user_id(),),
            )
            after = cursor.fetchone()["cnt"]
            conn.close()

        assert after == before + 1

    def test_valid_post_redirects_to_profile(self, auth_client):
        """Valid POST responds with a 302 redirect to /profile (PRG pattern)."""
        response = auth_client.post("/expenses/add", data=_valid_form())
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_valid_post_flash_success_message(self, auth_client):
        """Valid POST shows 'Expense added successfully.' flash after redirect to /profile."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(), follow_redirects=True
        )
        assert b"Expense added successfully." in response.data


# ---------------------------------------------------------------------------
# POST /expenses/add -- validation failures
# ---------------------------------------------------------------------------

class TestPostAddExpenseValidation:

    def test_missing_amount_rerenders_form_with_error(self, auth_client):
        """POST with a missing amount re-renders the form (200) with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(amount="")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_non_numeric_amount_rerenders_form_with_error(self, auth_client):
        """POST with non-numeric amount ('abc') re-renders the form with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(amount="abc")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_zero_amount_rerenders_form_with_error(self, auth_client):
        """POST with zero amount re-renders the form with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(amount="0")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_negative_amount_rerenders_form_with_error(self, auth_client):
        """POST with a negative amount re-renders the form with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(amount="-10.00")
        )
        assert response.status_code == 200
        assert b"valid amount" in response.data or b"Please enter" in response.data

    def test_future_date_rerenders_form_with_error(self, auth_client):
        """POST with a future date re-renders the form with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(date=_future_date())
        )
        assert response.status_code == 200
        assert (
            b"valid date" in response.data
            or b"future" in response.data
            or b"Please enter" in response.data
        )

    def test_invalid_category_rerenders_form_with_error(self, auth_client):
        """POST with a tampered/invalid category re-renders the form with an error flash."""
        response = auth_client.post(
            "/expenses/add", data=_valid_form(category="HackerCategory")
        )
        assert response.status_code == 200
        assert b"valid category" in response.data or b"Please select" in response.data

    def test_description_over_200_chars_rerenders_form_with_error(self, auth_client):
        """POST with a description longer than 200 characters re-renders the form with an error flash."""
        long_desc = "A" * 201
        response = auth_client.post(
            "/expenses/add", data=_valid_form(description=long_desc)
        )
        assert response.status_code == 200
        assert (
            b"200" in response.data
            or b"characters" in response.data
            or b"Description" in response.data
        )


# ---------------------------------------------------------------------------
# POST /expenses/add -- field value preservation on re-render
# ---------------------------------------------------------------------------

class TestPostAddExpenseFieldPreservation:

    def test_form_preserves_amount_on_validation_error(self, auth_client):
        """After a validation error, the submitted amount is preserved in the re-rendered form."""
        response = auth_client.post(
            "/expenses/add",
            data=_valid_form(amount="-5", category="Food"),
        )
        assert response.status_code == 200
        assert b"-5" in response.data

    def test_form_preserves_category_on_validation_error(self, auth_client):
        """After a validation error, the submitted category is preserved in the re-rendered form."""
        response = auth_client.post(
            "/expenses/add",
            data=_valid_form(date=_future_date(), category="Transport"),
        )
        assert response.status_code == 200
        assert b"Transport" in response.data

    def test_form_preserves_date_on_validation_error(self, auth_client):
        """After a validation error, the submitted date is preserved in the re-rendered form."""
        response = auth_client.post(
            "/expenses/add",
            data=_valid_form(amount="-1", date="2026-01-15"),
        )
        assert response.status_code == 200
        assert b"2026-01-15" in response.data

    def test_form_preserves_description_on_validation_error(self, auth_client):
        """After a validation error, the submitted description is preserved in the re-rendered form."""
        response = auth_client.post(
            "/expenses/add",
            data=_valid_form(amount="-1", description="My test note"),
        )
        assert response.status_code == 200
        assert b"My test note" in response.data


# ---------------------------------------------------------------------------
# POST /expenses/add -- empty description stored as NULL
# ---------------------------------------------------------------------------

class TestPostAddExpenseNullDescription:

    def test_empty_description_stored_as_null_not_empty_string(self, auth_client, app):
        """POST with empty description stores NULL (not empty string) in the DB."""
        auth_client.post(
            "/expenses/add",
            data=_valid_form(description=""),
        )

        with app.app_context():
            user_id = _get_test_user_id()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT description FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            row = cursor.fetchone()
            conn.close()

        assert row is not None, "No expense row was found after POST"
        assert row["description"] is None, (
            f"Expected NULL but got {row['description']!r}"
        )

    def test_whitespace_only_description_stored_as_null(self, auth_client, app):
        """POST with whitespace-only description stores NULL (not whitespace string) in the DB."""
        auth_client.post(
            "/expenses/add",
            data=_valid_form(description="   "),
        )

        with app.app_context():
            user_id = _get_test_user_id()
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT description FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            row = cursor.fetchone()
            conn.close()

        assert row is not None, "No expense row was found after POST"
        assert row["description"] is None, (
            f"Expected NULL but got {row['description']!r}"
        )


# ---------------------------------------------------------------------------
# POST /expenses/add -- unauthenticated
# ---------------------------------------------------------------------------

class TestPostAddExpenseUnauthenticated:

    def test_unauthenticated_post_redirects_to_login(self, client):
        """Unauthenticated POST to /expenses/add redirects to /login."""
        response = client.post("/expenses/add", data=_valid_form())
        assert response.status_code == 302
        assert "/login" in response.location

    def test_unauthenticated_post_flashes_login_error(self, client):
        """Unauthenticated POST to /expenses/add shows the login-required flash message."""
        response = client.post(
            "/expenses/add", data=_valid_form(), follow_redirects=True
        )
        assert b"Please log in to add an expense." in response.data


# ---------------------------------------------------------------------------
# Profile page CTA link
# ---------------------------------------------------------------------------

class TestProfileAddExpenseCTA:

    def test_profile_contains_link_to_add_expense(self, auth_client):
        """The /profile page contains a visible link pointing to /expenses/add."""
        response = auth_client.get("/profile")
        assert response.status_code == 200
        assert b"/expenses/add" in response.data
