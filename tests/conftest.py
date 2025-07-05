import pytest
from note_app import database
import sqlite3

@pytest.fixture
def db_conn():
    """
    Pytest fixture to set up a temporary, in-memory database for testing.
    It creates the schema and yields the connection object.
    """
    # Use an in-memory SQLite database for testing
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # We need to temporarily point the database module to this connection
    # This is a bit of a hack, but it's the simplest way for this structure.
    # A better way would be dependency injection.
    
    # Create the schema
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    );
    CREATE TABLE categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(name, user_id)
    );
    CREATE TABLE tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(name, user_id)
    );
    CREATE TABLE notes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        category_id TEXT,
        user_id TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    CREATE TABLE note_tags (
        note_id TEXT NOT NULL,
        tag_id TEXT NOT NULL,
        PRIMARY KEY (note_id, tag_id),
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    
    # Yield the connection to the test function
    yield conn
    
    # Teardown: close the connection after the test is done
    conn.close()