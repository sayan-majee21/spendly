import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=50, deadline=None)
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
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30, deadline=None)
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
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=30, deadline=None)
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

@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10, deadline=None)
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: '\0' not in x),
    email=st.emails(),
    password=st.text(min_size=1, max_size=50).filter(lambda x: '\0' not in x)
)
def test_login_redirection_property(client, name, email, password):
    """
    Property: Any successfully registered user should be redirected 
    to their profile page upon login.
    """
    # Ensure fresh session for each example
    with client.session_transaction() as sess:
        sess.clear()

    # Clear and register
    conn = get_db()
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    
    create_user(name, email, password)

    # Login
    response = client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    
    # Assert redirection to profile
    assert response.status_code == 200
    assert b"By Category" in response.data
    assert b"Recent Transactions" in response.data
@pytest.mark.hypothesis
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=10, deadline=None)
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: '\0' not in x),
    email=st.emails(),
    password=st.text(min_size=1, max_size=50).filter(lambda x: '\0' not in x),
    expenses=st.lists(
        st.tuples(
            st.floats(min_value=1.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
            st.sampled_from(["Food", "Transport", "Bills", "Entertainment", "Health"]),
            st.just("2026-06-16"),
            st.text(min_size=1, max_size=50).filter(lambda x: '\0' not in x)
        ),
        min_size=1,
        max_size=10
    )
)
def test_profile_stats_correctness(client, name, email, password, expenses):
    """
    Property: The Profile page should correctly display the sum and count 
     of all expenses added to the database for that user.
    """
    with client.session_transaction() as sess:
        sess.clear()

    conn = get_db()
    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM users")
    conn.commit()
    
    # Create user
    create_user(name, email, password)
    user = get_user_by_email(email)
    user_id = user['id']

    # Add expenses
    total_sum = 0
    for amount, category, date, desc in expenses:
        conn.execute('''
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, category, date, desc))
        total_sum += amount
    conn.commit()
    conn.close()

    # Login
    client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

    # Check Profile
    response = client.get('/profile')
    
    # Verify Transaction Count
    expected_count = f">{len(expenses)}</div>".encode('utf-8')
    assert expected_count in response.data

    # Verify Total Spent (formatted with comma and two decimals)
    # Note: ₹ symbol might be encoded or literal depending on template
    expected_sum_str = f"₹{total_sum:,.2f}".encode('utf-8')
    assert expected_sum_str in response.data

