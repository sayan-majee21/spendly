import pytest
from flask import url_for
from database.db import get_db, create_user

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

def test_analytics_unauthorized_redirect(client):
    """Security: Accessing /analytics without login redirects to /login."""
    response = client.get('/analytics')
    assert response.status_code == 302
    assert response.location.endswith('/login')
    
    # Follow redirect to verify flash message is displayed
    response_redirect = client.get('/analytics', follow_redirects=True)
    assert b"Please log in to view the analytics page." in response_redirect.data

def test_analytics_authorized_render(auth_client):
    """Happy path: GET /analytics should render coming soon page successfully for logged-in users."""
    response = auth_client.get('/analytics')
    assert response.status_code == 200
    assert b"Analytics Dashboard" in response.data
    assert b"Feature Preview" in response.data
    assert b"Visual Spending Trends" in response.data
    assert b"Advanced Category Distribution" in response.data

def test_navbar_active_highlighting(auth_client):
    """Happy path: Nav bar active item class highlights correctly depending on current endpoint."""
    # Visit /analytics
    response = auth_client.get('/analytics')
    assert response.status_code == 200
    # Analytics link should be active
    assert b'href="/analytics" class="active"' in response.data
    # Profile link should not be active
    assert b'href="/profile" class=""' in response.data or b'class="active"' not in response.data.split(b'href="/profile"')[1].split(b'>')[0]

    # Visit /profile
    response = auth_client.get('/profile')
    assert response.status_code == 200
    # Profile link should be active
    assert b'href="/profile" class="active"' in response.data
    # Analytics link should not be active
    assert b'href="/analytics" class=""' in response.data
