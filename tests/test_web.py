
import pytest
from note_app import database

def test_logged_out_redirect(client):
    """
    Tests that a logged-out user is redirected from the home page.
    """
    response = client.get('/')
    # Expect a 302 redirect status code
    assert response.status_code == 302
    # Expect the redirect to go to the login page
    assert 'login' in response.headers['Location']

def test_register_and_login(client):
    """
    Tests the full user registration and login flow.
    """
    # Test registration
    register_response = client.post('/register', data={
        'username': 'webtestuser',
        'email': 'web@test.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert register_response.status_code == 200
    # After successful registration, we should be on the login page
    # and see a success message.
    assert b'Registration successful! Please log in.' in register_response.data

    # Test login
    login_response = client.post('/login', data={
        'username': 'webtestuser',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert login_response.status_code == 200
    # After successful login, we should be on the home page
    # and see a welcome message.
    assert b'Welcome, webtestuser!' in login_response.data
    assert b'All Notes' in login_response.data

def test_failed_login(client):
    """
    Tests that a login with incorrect credentials fails.
    """
    # First, register a user to ensure they exist
    client.post('/register', data={
        'username': 'webtestuser',
        'email': 'web@test.com',
        'password': 'password123'
    }, follow_redirects=True)

    # Now, attempt to log in with a bad password
    login_response = client.post('/login', data={
        'username': 'webtestuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert login_response.status_code == 200
    # We should be back on the login page with an error message.
    assert b'Invalid username or password.' in login_response.data
    assert b'Welcome, webtestuser!' not in login_response.data

def test_logged_in_access(client):
    """
    Tests that a logged-in user can access the home page.
    """
    # Register and log in the user
    client.post('/register', data={'username': 'test', 'email': 'test@test.com', 'password': 'pw'})
    client.post('/login', data={'username': 'test', 'password': 'pw'})

    # Now, access the home page
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'All Notes' in response.data
