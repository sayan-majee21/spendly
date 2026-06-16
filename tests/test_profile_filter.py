import pytest
from flask import url_for
from database.db import get_db, create_user
import sqlite3

@pytest.fixture
def auth_client(client, app):
    """A test client that is already logged in."""
    with app.app_context():
        create_user("Test User", "test@example.com", "password123")
    
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    return client

def seed_test_expenses(user_id):
    """Seed expenses with specific dates for testing filters."""
    conn = get_db()
    cursor = conn.cursor()
    expenses = [
        (user_id, 100.0, 'Food', '2026-01-01', 'New Year Dinner'),
        (user_id, 50.0, 'Transport', '2026-02-01', 'Train ticket'),
        (user_id, 200.0, 'Bills', '2026-03-01', 'Electricity'),
        (user_id, 150.0, 'Food', '2026-03-15', 'Grocery'),
        (user_id, 300.0, 'Shopping', '2026-04-01', 'Clothes'),
    ]
    cursor.executemany(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
        expenses
    )
    conn.commit()
    conn.close()

def get_test_user_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', ('test@example.com',))
    user_id = cursor.fetchone()['id']
    conn.close()
    return user_id

def test_profile_unfiltered_shows_all(auth_client, app):
    """Happy path: GET /profile with no parameters should show all expenses."""
    with app.app_context():
        user_id = get_test_user_id()
        seed_test_expenses(user_id)

    response = auth_client.get('/profile')
    assert response.status_code == 200
    
    # Check total spent (100 + 50 + 200 + 150 + 300 = 800)
    assert b'\xe2\x82\xb9800.00' in response.data # \xe2\x82\xb9 is ₹
    # Check transaction count
    assert b'5' in response.data
    # Check all transactions are present
    assert b'New Year Dinner' in response.data
    assert b'Train ticket' in response.data
    assert b'Electricity' in response.data
    assert b'Grocery' in response.data
    assert b'Clothes' in response.data

def test_profile_filtered_valid_range(auth_client, app):
    """Happy path: GET /profile?date_from=...&date_to=... should filter results."""
    with app.app_context():
        user_id = get_test_user_id()
        seed_test_expenses(user_id)

    # Filter for March 2026
    response = auth_client.get('/profile?date_from=2026-03-01&date_to=2026-03-31')
    assert response.status_code == 200
    
    # Check total spent (200 + 150 = 350)
    assert b'\xe2\x82\xb9350.00' in response.data
    # Check transaction count
    assert b'2' in response.data
    # Check filtered transactions
    assert b'Electricity' in response.data
    assert b'Grocery' in response.data
    # Check items outside range are NOT present
    assert b'New Year Dinner' not in response.data
    assert b'Clothes' not in response.data

def test_profile_filtered_invalid_range_fallbacks(auth_client, app):
    """Error path: Start date > End date should fallback to unfiltered and show error."""
    with app.app_context():
        user_id = get_test_user_id()
        seed_test_expenses(user_id)

    response = auth_client.get('/profile?date_from=2026-12-31&date_to=2026-01-01', follow_redirects=True)
    assert response.status_code == 200
    
    # Check flash message
    assert b'Start date must be before end date.' in response.data
    # Check it fallback to all (total 800)
    assert b'\xe2\x82\xb9800.00' in response.data

def test_profile_filtered_malformed_dates_fallbacks(auth_client, app):
    """Edge case: Malformed dates should silently fallback to unfiltered."""
    with app.app_context():
        user_id = get_test_user_id()
        seed_test_expenses(user_id)

    response = auth_client.get('/profile?date_from=invalid&date_to=2026-01-01')
    assert response.status_code == 200
    
    # Check it fallback to all (total 800)
    assert b'\xe2\x82\xb9800.00' in response.data

def test_profile_filtered_no_results(auth_client, app):
    """Edge case: A range with no expenses should show zero stats."""
    with app.app_context():
        user_id = get_test_user_id()
        seed_test_expenses(user_id)

    response = auth_client.get('/profile?date_from=2020-01-01&date_to=2020-12-31')
    assert response.status_code == 200
    
    # Check total spent is 0
    assert b'\xe2\x82\xb90.00' in response.data
    # Check transaction count is 0
    assert b'0' in response.data
    # Check top category is None
    assert b'None' in response.data
    # Check no transactions are in the list (their descriptions shouldn't be there)
    assert b'New Year Dinner' not in response.data

def test_profile_auth_required(client):
    """Security: Accessing /profile without login redirects to /login."""
    response = client.get('/profile')
    assert response.status_code == 302
    assert response.location.endswith('/login')

def test_profile_presets_work(auth_client, app):
    """Happy path: Preset buttons should lead to filtered results."""
    response = auth_client.get('/profile')
    assert response.status_code == 200
    
    assert b'This Month' in response.data
    assert b'Last 3 Months' in response.data
    assert b'Last 6 Months' in response.data
    assert b'All Time' in response.data
    
    # Verify the "All Time" link is just /profile
    assert b'href="/profile"' in response.data or b"href='/profile'" in response.data
