
import sqlite3
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'notes.db'

def setup_database():
    """Creates the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # User table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')

    # Categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # Tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        user_id TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # Notes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        category_id TEXT,
        user_id TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES categories (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')

    # Note-Tags junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS note_tags (
        note_id TEXT NOT NULL,
        tag_id TEXT NOT NULL,
        PRIMARY KEY (note_id, tag_id),
        FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()

def create_user(username, email, password):
    """Creates a new user with a hashed password."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(password)
    try:
        cursor.execute(
            "INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)",
            (user_id, username, email, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # This happens if username or email is not unique
        return None
    finally:
        conn.close()
    return user_id

def get_user_by_username(username):
    """Retrieves a user by their username."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def verify_password(username, password):
    """Verifies a user's password."""
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        return user
    return None

def _get_or_create_category(cursor, category_name, user_id):
    """Gets the ID of a category for a specific user, creating it if it doesn't exist."""
    if not category_name:
        return None
    cursor.execute("SELECT id FROM categories WHERE name = ? AND user_id = ?", (category_name, user_id))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        new_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO categories (id, name, user_id) VALUES (?, ?, ?)", (new_id, category_name, user_id))
        return new_id

def _get_or_create_tags(cursor, tag_names_str, user_id):
    """Gets the IDs of tags for a specific user, creating them if they don't exist."""
    if not tag_names_str:
        return []
    tag_names = [tag.strip() for tag in tag_names_str.split(',') if tag.strip()]
    tag_ids = []
    for name in tag_names:
        cursor.execute("SELECT id FROM tags WHERE name = ? AND user_id = ?", (name, user_id))
        result = cursor.fetchone()
        if result:
            tag_ids.append(result[0])
        else:
            new_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO tags (id, name, user_id) VALUES (?, ?, ?)", (new_id, name, user_id))
            tag_ids.append(new_id)
    return tag_ids

def add_note(title, content, category_name, tags_str, user_id):
    """Adds a new note to the database for a specific user and returns its ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    category_id = _get_or_create_category(cursor, category_name, user_id)
    tag_ids = _get_or_create_tags(cursor, tags_str, user_id)
    note_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO notes (id, title, content, timestamp, category_id, user_id) VALUES (?, ?, ?, ?, ?, ?)",
        (note_id, title, content, timestamp, category_id, user_id)
    )
    for tag_id in tag_ids:
        cursor.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    conn.commit()
    conn.close()
    return note_id

def get_all_categories(user_id):
    """Fetches all categories for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE user_id = ? ORDER BY name", (user_id,))
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

def list_notes(user_id, category_name=None):
    """Lists the last 10 notes for a user, optionally filtered by category."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.user_id = ?
    """
    params = [user_id]
    if category_name:
        query += " AND c.name = ?"
        params.append(category_name)
    query += " GROUP BY n.id ORDER BY n.timestamp DESC LIMIT 10"
    cursor.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def get_note(note_id, user_id):
    """Retrieves a single note by its UUID, ensuring it belongs to the user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id = ? AND n.user_id = ?
        GROUP BY n.id
    """, (note_id, user_id))
    note = cursor.fetchone()
    conn.close()
    return dict(note) if note else None

def update_note_content(note_id, new_content, user_id):
    """DEPRECATED. Use update_note instead. Updates the content of a specific note."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Ensure the note belongs to the user before updating
    cursor.execute("UPDATE notes SET content = ? WHERE id = ? AND user_id = ?", (new_content, note_id, user_id))
    conn.commit()
    conn.close()

def delete_note(note_id, user_id):
    """Deletes a note and its tag associations, ensuring it belongs to the user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # First, verify the note belongs to the user
    cursor.execute("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    if cursor.fetchone():
        cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
    conn.close()

def search_notes(keyword, user_id):
    """Searches for notes containing a keyword for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.user_id = ? AND (n.title LIKE ? OR n.content LIKE ?)
        GROUP BY n.id ORDER BY n.timestamp DESC
    """
    params = [user_id, f'%{keyword}%', f'%{keyword}%']
    cursor.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def update_note(note_id, title, content, category_name, tags_str, user_id):
    """Updates all fields of a specific note for a given user."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Ensure the note belongs to the user before updating
    cursor.execute("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    if cursor.fetchone():
        category_id = _get_or_create_category(cursor, category_name, user_id)
        cursor.execute(
            "UPDATE notes SET title = ?, content = ?, category_id = ? WHERE id = ?",
            (title, content, category_id, note_id)
        )
        # Update tags
        cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        tag_ids = _get_or_create_tags(cursor, tags_str, user_id)
        for tag_id in tag_ids:
            cursor.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
        conn.commit()
    conn.close()

def search_by_tag(tag_name, user_id):
    """Searches for notes by a specific tag for a given user."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.user_id = ? AND n.id IN (
            SELECT note_id FROM note_tags WHERE tag_id IN (
                SELECT id FROM tags WHERE name = ? AND user_id = ?
            )
        )
        GROUP BY n.id ORDER BY n.timestamp DESC
    """
    cursor.execute(query, (user_id, tag_name, user_id))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes
