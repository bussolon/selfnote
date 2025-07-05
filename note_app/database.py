import sqlite3
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'notes.db'

def get_db_conn():
    """Helper to create a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Creates the database and tables if they don't exist."""
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(name, user_id)
        )''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(name, user_id)
        )''')
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            PRIMARY KEY (note_id, tag_id),
            FOREIGN KEY (note_id) REFERENCES notes (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )''')
        conn.commit()

# --- User Functions ---

def create_user(username, email, password, db_conn=None):
    conn = db_conn or get_db_conn()
    user_id = str(uuid.uuid4())
    hashed_password = generate_password_hash(password)
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (id, username, email, password) VALUES (?, ?, ?, ?)",
                (user_id, username, email, hashed_password)
            )
    except sqlite3.IntegrityError:
        return None
    finally:
        if not db_conn: conn.close()
    return user_id

def get_user_by_username(username, db_conn=None):
    conn = db_conn or get_db_conn()
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not db_conn: conn.close()
    return dict(user) if user else None

def verify_password(username, password, db_conn=None):
    user = get_user_by_username(username, db_conn=db_conn)
    if user and check_password_hash(user['password'], password):
        return user
    return None

# --- Note & Metadata Functions ---

def _get_or_create_category(conn, category_name, user_id):
    if not category_name: return None
    cursor = conn.execute("SELECT id FROM categories WHERE name = ? AND user_id = ?", (category_name, user_id))
    result = cursor.fetchone()
    if result: return result['id']
    new_id = str(uuid.uuid4())
    conn.execute("INSERT INTO categories (id, name, user_id) VALUES (?, ?, ?)", (new_id, category_name, user_id))
    return new_id

def _get_or_create_tags(conn, tag_names_str, user_id):
    if not tag_names_str: return []
    tag_names = [tag.strip() for tag in tag_names_str.split(',') if tag.strip()]
    tag_ids = []
    for name in tag_names:
        cursor = conn.execute("SELECT id FROM tags WHERE name = ? AND user_id = ?", (name, user_id))
        result = cursor.fetchone()
        if result:
            tag_ids.append(result['id'])
        else:
            new_id = str(uuid.uuid4())
            conn.execute("INSERT INTO tags (id, name, user_id) VALUES (?, ?, ?)", (new_id, name, user_id))
            tag_ids.append(new_id)
    return tag_ids

def add_note(title, content, category_name, tags_str, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    note_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        category_id = _get_or_create_category(conn, category_name, user_id)
        tag_ids = _get_or_create_tags(conn, tags_str, user_id)
        conn.execute(
            "INSERT INTO notes (id, title, content, timestamp, category_id, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (note_id, title, content, timestamp, category_id, user_id)
        )
        for tag_id in tag_ids:
            conn.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    if not db_conn: conn.close()
    return note_id

def get_note(note_id, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    cursor = conn.execute("""
        SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id = ? AND n.user_id = ?
        GROUP BY n.id
    """, (note_id, user_id))
    note = cursor.fetchone()
    if not db_conn: conn.close()
    return dict(note) if note else None

def list_notes(user_id, category_name=None, db_conn=None):
    conn = db_conn or get_db_conn()
    query = "SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags FROM notes n LEFT JOIN categories c ON n.category_id = c.id LEFT JOIN note_tags nt ON n.id = nt.note_id LEFT JOIN tags t ON nt.tag_id = t.id WHERE n.user_id = ?"
    params = [user_id]
    if category_name:
        query += " AND c.name = ?"
        params.append(category_name)
    query += " GROUP BY n.id ORDER BY n.timestamp DESC LIMIT 10"
    cursor = conn.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    if not db_conn: conn.close()
    return notes

def update_note(note_id, title, content, category_name, tags_str, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    with conn:
        cursor = conn.execute("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        if cursor.fetchone():
            category_id = _get_or_create_category(conn, category_name, user_id)
            conn.execute(
                "UPDATE notes SET title = ?, content = ?, category_id = ? WHERE id = ?",
                (title, content, category_id, note_id)
            )
            conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
            tag_ids = _get_or_create_tags(conn, tags_str, user_id)
            for tag_id in tag_ids:
                conn.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    if not db_conn: conn.close()

def delete_note(note_id, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    with conn:
        cursor = conn.execute("SELECT id FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
        if cursor.fetchone():
            conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    if not db_conn: conn.close()

def search_notes(keyword, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    query = "SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags FROM notes n LEFT JOIN categories c ON n.category_id = c.id LEFT JOIN note_tags nt ON n.id = nt.note_id LEFT JOIN tags t ON nt.tag_id = t.id WHERE n.user_id = ? AND (n.title LIKE ? OR n.content LIKE ?) GROUP BY n.id ORDER BY n.timestamp DESC"
    params = [user_id, f'%{keyword}%', f'%{keyword}%']
    cursor = conn.execute(query, params)
    notes = [dict(row) for row in cursor.fetchall()]
    if not db_conn: conn.close()
    return notes

def search_by_tag(tag_name, user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    query = "SELECT n.id, n.timestamp, n.title, n.content, c.name as category, GROUP_CONCAT(t.name, ', ') as tags FROM notes n LEFT JOIN categories c ON n.category_id = c.id LEFT JOIN note_tags nt ON n.id = nt.note_id LEFT JOIN tags t ON nt.tag_id = t.id WHERE n.user_id = ? AND n.id IN (SELECT note_id FROM note_tags WHERE tag_id IN (SELECT id FROM tags WHERE name = ? AND user_id = ?)) GROUP BY n.id ORDER BY n.timestamp DESC"
    cursor = conn.execute(query, (user_id, tag_name, user_id))
    notes = [dict(row) for row in cursor.fetchall()]
    if not db_conn: conn.close()
    return notes

def get_all_categories(user_id, db_conn=None):
    conn = db_conn or get_db_conn()
    cursor = conn.execute("SELECT name FROM categories WHERE user_id = ? ORDER BY name", (user_id,))
    categories = [row[0] for row in cursor.fetchall()]
    if not db_conn: conn.close()
    return categories