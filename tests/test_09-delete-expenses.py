import pytest
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
# GET /expenses/<id>/delete
# ---------------------------------------------------------------------------

class TestDeleteExpense:

    def test_delete_unauthenticated_redirects(self, client):
        """GET /expenses/1/delete redirects to /login for unlogged users."""
        response = client.get("/expenses/1/delete")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_delete_unauthenticated_flashes_error(self, client):
        """GET /expenses/1/delete flashes correct error message for unlogged users."""
        response = client.get("/expenses/1/delete", follow_redirects=True)
        assert b"Please log in to delete an expense." in response.data

    def test_delete_nonexistent_redirects(self, auth_client):
        """GET /expenses/9999/delete redirects to /profile if expense does not exist."""
        response = auth_client.get("/expenses/9999/delete")
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_delete_nonexistent_flashes_error(self, auth_client):
        """GET /expenses/9999/delete flashes 'Expense not found.' error."""
        response = auth_client.get("/expenses/9999/delete", follow_redirects=True)
        assert b"Expense not found." in response.data

    def test_delete_unauthorized_redirects(self, auth_client, app):
        """GET /expenses/<id>/delete redirects to /profile if expense belongs to another user."""
        with app.app_context():
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", "2026-06-20", "Other user's bill")

        response = auth_client.get(f"/expenses/{other_expense_id}/delete")
        assert response.status_code == 302
        assert "/profile" in response.location

    def test_delete_unauthorized_flashes_error(self, auth_client, app):
        """GET /expenses/<id>/delete flashes 'You are not authorized to delete this expense.'."""
        with app.app_context():
            create_user("Other User", "other@example.com", "password123")
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", ("other@example.com",))
            other_user_id = cursor.fetchone()["id"]
            conn.close()
            other_expense_id = _insert_test_expense(other_user_id, 100.0, "Bills", "2026-06-20", "Other user's bill")

        response = auth_client.get(f"/expenses/{other_expense_id}/delete", follow_redirects=True)
        assert b"You are not authorized to delete this expense." in response.data

    def test_delete_success(self, auth_client, app):
        """Valid delete request deletes the expense, redirects to /profile with success flash."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 42.50, "Food", "2026-06-15", "Description to delete")

        # Verify expense exists before delete
        response = auth_client.get("/profile")
        assert b"Description to delete" in response.data

        # Delete
        response = auth_client.get(f"/expenses/{expense_id}/delete", follow_redirects=True)
        assert response.status_code == 200
        assert b"Expense deleted successfully." in response.data
        assert b"Description to delete" not in response.data

        # Check DB
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            conn.close()
            assert row is None

    def test_delete_database_failure(self, auth_client, app):
        """If database deletion fails, displays error message and redirects to /profile."""
        with app.app_context():
            user_id = _get_test_user_id()
            expense_id = _insert_test_expense(user_id, 42.50, "Food", "2026-06-15", "Fail description")

        # Mock db_delete_expense to return False
        with patch("app.db_delete_expense", return_value=False):
            response = auth_client.get(f"/expenses/{expense_id}/delete", follow_redirects=True)

        assert response.status_code == 200
        assert b"Something went wrong. Please try again." in response.data

        # Check DB to confirm it was not deleted
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
            row = cursor.fetchone()
            conn.close()
            assert row is not None
