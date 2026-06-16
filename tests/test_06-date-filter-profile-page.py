import pytest
from flask import url_for
from database.db import get_db, create_user
from datetime import date, timedelta

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
    row = cursor.fetchone()
    user_id = row['id']
    conn.close()
    return user_id

class TestProfileDateFilter:
    
    def test_auth_guard(self, client):
        """Unauthenticated requests to /profile should redirect to /login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_profile_unfiltered_shows_all(self, auth_client, app):
        """Happy path: GET /profile with no parameters shows all data (Step 5 behavior)."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)

        response = auth_client.get('/profile')
        assert response.status_code == 200
        
        # Summary Stats (Total: 100+50+200+150+300 = 800)
        assert b'\xe2\x82\xb9800.00' in response.data  # ₹800.00
        assert b'5' in response.data  # Transaction count
        
        # Recent Transactions
        assert b'New Year Dinner' in response.data
        assert b'Train ticket' in response.data
        assert b'Electricity' in response.data
        assert b'Grocery' in response.data
        assert b'Clothes' in response.data
        
        # Category Breakdown
        assert b'Food' in response.data
        assert b'Transport' in response.data
        assert b'Bills' in response.data
        assert b'Shopping' in response.data

    def test_profile_custom_range_filtering(self, auth_client, app):
        """Happy path: Valid date_from and date_to filters all sections correctly."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)

        # Filter for March 2026
        response = auth_client.get('/profile?date_from=2026-03-01&date_to=2026-03-31')
        assert response.status_code == 200
        
        # Summary Stats (March expenses: 200 + 150 = 350)
        assert b'\xe2\x82\xb9350.00' in response.data
        assert b'2' in response.data
        
        # Recent Transactions
        assert b'Electricity' in response.data
        assert b'Grocery' in response.data
        assert b'New Year Dinner' not in response.data
        assert b'Train ticket' not in response.data
        assert b'Clothes' not in response.data
        
        # Category Breakdown
        assert b'Bills' in response.data
        assert b'Food' in response.data
        assert b'Transport' not in response.data
        assert b'Shopping' not in response.data

    def test_invalid_date_range_error(self, auth_client, app):
        """Validation: If date_from > date_to, flash error and show unfiltered view."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)

        response = auth_client.get('/profile?date_from=2026-12-31&date_to=2026-01-01', follow_redirects=True)
        assert response.status_code == 200
        
        # Should show flash error
        assert b'Start date must be before end date.' in response.data
        
        # Should fall back to unfiltered (Total 800)
        assert b'\xe2\x82\xb9800.00' in response.data

    def test_malformed_dates_fallback(self, auth_client, app):
        """Validation: Malformed date strings should silently fallback to unfiltered."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)

        response = auth_client.get('/profile?date_from=not-a-date&date_to=2026-03-31')
        assert response.status_code == 200
        
        # Should fall back to unfiltered (Total 800)
        assert b'\xe2\x82\xb9800.00' in response.data

    def test_empty_results_in_range(self, auth_client, app):
        """Edge case: Range with no expenses shows zeroed stats and empty lists."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)

        # Filter for a year with no data
        response = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-12-31')
        assert response.status_code == 200
        
        # Stats should be 0
        assert b'\xe2\x82\xb90.00' in response.data
        assert b'0' in response.data
        assert b'None' in response.data # Top category
        
        # Transactions should be empty
        assert b'New Year Dinner' not in response.data
        
        # Category breakdown should be empty (assuming no categories shown if 0)
        assert b'Food' not in response.data

    def test_ui_elements_presence(self, auth_client):
        """Template: Verify filter bar and preset buttons are present."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        
        # Quick-select presets
        assert b'This Month' in response.data
        assert b'Last 3 Months' in response.data
        assert b'Last 6 Months' in response.data
        assert b'All Time' in response.data
        
        # Custom range form
        assert b'date_from' in response.data
        assert b'date_to' in response.data
        assert b'Apply' in response.data or b'apply' in response.data.lower()

    def test_active_state_highlighting(self, auth_client):
        """Template: Verify active range is reflected in UI."""
        # Custom range
        date_from = '2026-03-01'
        date_to = '2026-03-31'
        response = auth_client.get(f'/profile?date_from={date_from}&date_to={date_to}')
        assert response.status_code == 200
        
        # Input values should match
        assert f'value="{date_from}"'.encode() in response.data
        assert f'value="{date_to}"'.encode() in response.data

    @pytest.mark.parametrize("preset", ["This Month", "Last 3 Months", "Last 6 Months", "All Time"])
    def test_preset_links_structure(self, auth_client, preset):
        """Template: Preset links should be present and formatted correctly."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        
        # Check that the preset text is within a link or button
        assert preset.encode() in response.data
        
        if preset == "All Time":
            # All Time should link back to /profile with no params
            # Note: could be href="/profile" or href="http://localhost/profile"
            assert b'href="/profile"' in response.data or b"href='/profile'" in response.data
        else:
            # Other presets should have date_from and date_to params
            assert b'date_from=' in response.data
            assert b'date_to=' in response.data

    def test_db_side_effects_on_filtering(self, auth_client, app):
        """DB: Verify that filtering doesn't accidentally modify data."""
        with app.app_context():
            user_id = get_test_user_id()
            seed_test_expenses(user_id)
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM expenses WHERE user_id = ?', (user_id,))
            initial_count = cursor.fetchone()['count']
            conn.close()

        # Apply a filter
        auth_client.get('/profile?date_from=2026-03-01&date_to=2026-03-31')
        
        # Verify count remains same in DB
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM expenses WHERE user_id = ?', (user_id,))
            final_count = cursor.fetchone()['count']
            conn.close()
            assert initial_count == final_count
