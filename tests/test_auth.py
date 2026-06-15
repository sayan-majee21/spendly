import pytest
from flask import session
from app import app

def test_registration(client):
    """Test user registration."""
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    # Check if registration was successful
    assert b"Registration successful! Please log in." in response.data
    # Check if we are on the login page
    assert b"Welcome back" in response.data

def test_login_logout(client):
    """Test user login and logout."""
    # Register first
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })

    # Test login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    # Verify redirect to profile page
    assert response.status_code == 200
    assert b"By Category" in response.data # Profile specific content
    assert b"Total Spent" in response.data # Profile specific content
    
    # Verify session using session_transaction
    with client.session_transaction() as sess:
        assert sess['user_id'] is not None
        assert sess['user_name'] == 'Test User'

    # Test logout
    response = client.get('/logout', follow_redirects=True)
    assert b"Logged out successfully." in response.data
    
    # Verify session cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_invalid_login(client):
    """Test login with invalid credentials."""
    # Register a user first
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })

    # Wrong password
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b"Invalid email or password." in response.data

    # Non-existent email
    response = client.post('/login', data={
        'email': 'nobody@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert b"Invalid email or password." in response.data

def test_logged_in_redirection(client):
    """Test that logged-in users are redirected away from login/register pages."""
    # Register and login
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })

    # Try to access login page
    response = client.get('/login', follow_redirects=True)
    assert b"Track every rupee" in response.data # Redirected to landing

    # Try to access register page
    response = client.get('/register', follow_redirects=True)
    assert b"Track every rupee" in response.data # Redirected to landing
