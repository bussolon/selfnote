import pytest
import tempfile
import os
from note_app import web, database

@pytest.fixture
def app():
    """
    Create and configure a new app instance for each test.
    """
    # Create a temporary file to be the database
    db_fd, db_path = tempfile.mkstemp()

    # Create the Flask app configured for testing
    app = web.create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    # Set the database name for the database module
    database.DB_NAME = db_path

    # Create the database and the tables
    with app.app_context():
        database.setup_database()

    yield app

    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()