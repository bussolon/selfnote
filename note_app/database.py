
import sqlite3
import uuid
from datetime import datetime

DB_NAME = 'notes.db'

def setup_database():
    """Creates the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        category_id TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS note_tags (
        note_id TEXT NOT NULL,
        tag_id TEXT NOT NULL,
        PRIMARY KEY (note_id, tag_id),
        FOREIGN KEY (note_id) REFERENCES notes (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
    )''')
    conn.commit()
    conn.close()

def _get_or_create_category(cursor, category_name):
    """Gets the ID of a category, creating it if it doesn't exist."""
    if not category_name:
        return None
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        new_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO categories (id, name) VALUES (?, ?)", (new_id, category_name))
        return new_id

def _get_or_create_tags(cursor, tag_names_str):
    """Gets the IDs of tags, creating them if they don't exist."""
    if not tag_names_str:
        return []
    tag_names = [tag.strip() for tag in tag_names_str.split(',') if tag.strip()]
    tag_ids = []
    for name in tag_names:
        cursor.execute("SELECT id FROM tags WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            tag_ids.append(result[0])
        else:
            new_id = str(uuid.uuid4())
            cursor.execute("INSERT INTO tags (id, name) VALUES (?, ?)", (new_id, name))
            tag_ids.append(new_id)
    return tag_ids

def add_note(title, content, category_name, tags_str):
    """Adds a new note to the database and returns its ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    category_id = _get_or_create_category(cursor, category_name)
    tag_ids = _get_or_create_tags(cursor, tags_str)
    note_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO notes (id, title, content, timestamp, category_id) VALUES (?, ?, ?, ?, ?)",
        (note_id, title, content, timestamp, category_id)
    )
    for tag_id in tag_ids:
        cursor.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    conn.commit()
    conn.close()
    return note_id

def get_all_categories():
    """Fetches all categories from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories ORDER BY name")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

def list_notes(category_name=None):
    """Lists the last 10 notes, optionally filtered by category."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
    """
    params = []
    if category_name:
        query += " WHERE c.name = ?"
        params.append(category_name)
    query += " GROUP BY n.id ORDER BY n.timestamp DESC LIMIT 10"
    cursor.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def get_note(note_id):
    """Retrieves a single note by its UUID."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id = ?
        GROUP BY n.id
    """, (note_id,))
    note = cursor.fetchone()
    conn.close()
    return dict(note) if note else None

def update_note_content(note_id, new_content):
    """Updates the content of a specific note."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET content = ? WHERE id = ?", (new_content, note_id))
    conn.commit()
    conn.close()

def delete_note(note_id):
    """Deletes a note and its tag associations."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()

def search_notes(keyword):
    """Searches for notes containing a keyword."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.title LIKE ? OR n.content LIKE ?
        GROUP BY n.id ORDER BY n.timestamp DESC
    """
    params = [f'%{keyword}%', f'%{keyword}%']
    cursor.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes

def search_by_tag(tag_name):
    """Searches for notes by a specific tag."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id IN (SELECT note_id FROM note_tags WHERE tag_id IN (SELECT id FROM tags WHERE name = ?))
        GROUP BY n.id ORDER BY n.timestamp DESC
    """
    cursor.execute(query, (tag_name,))
    notes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notes
