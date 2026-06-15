import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50)
@given(
    name=st.text(min_size=1, max_size=100),
    email=st.emails(),
    password=st.text(min_size=1, max_size=100)
)
def test_registration_properties(client, name, email, password):
    """
    Property: Registration should never cause a 500 error,
    regardless of the name, email, or password provided.
    """
    response = client.post('/register', data={
        'name': name,
        'email': email,
        'password': password
    }, follow_redirects=True)
    
    # We expect either a success redirect or a validation error message,
    # but NEVER a 500 Internal Server Error.
    assert response.status_code == 200
    
    # Check that we didn't crash
    assert b"Internal Server Error" not in response.data

@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
@given(
    email=st.emails() | st.text(),
    password=st.text()
)
def test_login_properties(client, email, password):
    """
    Property: Login should never cause a 500 error,
    even with non-email strings or empty passwords.
    """
    response = client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Internal Server Error" not in response.data

from database.db import create_user, get_user_by_email, get_db

@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30)
@given(
    name=st.text(min_size=1),
    email=st.emails(),
    password=st.text(min_size=1)
)
def test_database_create_user_properties(client, name, email, password):
    """
    Property: create_user should return True for new emails and 
    False for duplicate emails, never raising an exception.
    """
    # CLEAR TABLE TO ENSURE ISOLATION BETWEEN HYPOTHESIS EXAMPLES
    conn = get_db()
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()

    # First creation should succeed
    assert create_user(name, email, password) is True
    
    # Second creation with same email should return False (IntegrityError handled)
    assert create_user("Other Name", email, "other_pass") is False
    
    # Verify we can retrieve the user
    user = get_user_by_email(email)
    assert user is not None
    assert user['email'] == email
    assert user['name'] == name
