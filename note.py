
import re
import sqlite3
import argparse
import uuid
from datetime import datetime
import sys
import os
import subprocess
import tempfile

DB_NAME = 'notes.db'

def setup_database():
    """Creates the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )''')

    # Create tags table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )''')

    # Create notes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        category_id TEXT,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )''')

    # Create note_tags junction table
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

def get_or_create_category(cursor, category_name):
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

def get_or_create_tags(cursor, tag_names_str):
    """Gets the IDs of tags, creating them if they don't exist."""
    if not tag_names_str:
        return []
    tag_names = [tag.strip() for tag in tag_names_str.split(',')]
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
    """Adds a new note to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get or create category and tags
    category_id = get_or_create_category(cursor, category_name)
    tag_ids = get_or_create_tags(cursor, tags_str)

    # Insert the note
    note_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO notes (id, title, content, timestamp, category_id) VALUES (?, ?, ?, ?, ?)",
        (note_id, title, content, timestamp, category_id)
    )

    # Link note to tags
    for tag_id in tag_ids:
        cursor.execute("INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))

    conn.commit()
    conn.close()

def get_all_categories(cursor):
    """Fetches all categories from the database."""
    cursor.execute("SELECT name FROM categories ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def prompt_for_category(cursor):
    """Prompts the user to select an existing or new category."""
    print("\n--- Select a Category ---")
    categories = get_all_categories(cursor)
    if not categories:
        print("No categories found. Let's create one.")
        return input("Enter new category name: ")

    for i, name in enumerate(categories):
        print(f"{i + 1}: {name}")

    while True:
        choice = input("Choose a number or enter a new category name: ")
        if choice.isdigit() and 1 <= int(choice) <= len(categories):
            return categories[int(choice) - 1]
        elif choice:
            return choice
        # Allow empty input to mean no category
        print("Invalid choice. Please try again.")


def prompt_for_tags():
    """Prompts the user for optional tags."""
    print("\n--- Add Tags (Optional) ---")
    return input("Enter comma-separated tags, or press Enter to skip: ")


def list_notes(category_name=None):
    """Lists the last 10 notes, optionally filtered by category."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    base_query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name, GROUP_CONCAT(t.name, ', ')
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
    """
    params = []
    if category_name:
        base_query += " WHERE c.name = ?"
        params.append(category_name)

    base_query += """
        GROUP BY n.id
        ORDER BY n.timestamp DESC
        LIMIT 10
    """

    cursor.execute(base_query, params)
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        print(f"No notes found{f' in category {category_name}' if category_name else ''}.")
        return

    for note in notes:
        note_id, timestamp, title, content, category, tags = note
        print(f"---")
        print(f"ID: {note_id}")
        print(f"Date: {timestamp}")
        print(f"Title: {title}")
        if category:
            print(f"Category: {category}")
        if tags:
            print(f"Tags: {tags}")
        print(f"Body: {content[:100].replace(chr(10), ' ')}...")


def view_note(note_id):
    """Displays a single note by its UUID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT n.timestamp, n.title, n.content, c.name, GROUP_CONCAT(t.name, ', ')
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id = ?
        GROUP BY n.id
    """, (note_id,))

    note = cursor.fetchone()
    conn.close()

    if not note:
        print(f"No note found with ID: {note_id}")
        return

    timestamp, title, content, category, tags = note
    print(f"---")
    print(f"Title: {title}")
    print(f"Date: {timestamp}")
    if category:
        print(f"Category: {category}")
    if tags:
        print(f"Tags: {tags}")
    print(f"---\n{content}")


def save_note_as_markdown(note_id):
    """Saves a single note to a Markdown file with a YAML header."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch the note details
    cursor.execute("""
        SELECT n.id, n.timestamp, n.title, n.content, c.name, GROUP_CONCAT(t.name, ', ')
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id = ?
        GROUP BY n.id
    """, (note_id,))
    note = cursor.fetchone()
    conn.close()

    if not note:
        print(f"No note found with ID: {note_id}")
        return

    note_uuid, timestamp_str, title, content, category, tags_str = note

    # Sanitize title for filename
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)

    # Format date for filename
    date_obj = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    filename = f"{date_obj.strftime('%Y_%m_%d')}_{safe_title}.md"

    # Build YAML header
    yaml_header = "---\n"
    yaml_header += f"uuid: {note_uuid}\n"
    yaml_header += f"title: \"{title}\"\n"
    if category:
        yaml_header += f"category: {category}\n"
    if tags_str:
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        yaml_header += "tags:\n"
        for tag in tags_list:
            yaml_header += f"  - {tag}\n"
    yaml_header += "---\n\n"

    # Write to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(yaml_header)
            f.write(content)
        print(f"Note successfully saved to: {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")


def delete_note(note_id):
    """Deletes a note after confirmation."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT title FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    if not note:
        print(f"No note found with ID: {note_id}")
        conn.close()
        return

    title = note[0]
    confirm = input(f'Are you sure you want to delete "{title}"? [y/N]: ')
    if confirm.lower() == 'y':
        cursor.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        print(f'Note "{title}" has been deleted.')
    else:
        print("Deletion cancelled.")
    
    conn.close()

def edit_note(note_id):
    """Opens a note's content in 'micro' for editing."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT content FROM notes WHERE id = ?", (note_id,))
    note = cursor.fetchone()

    if not note:
        print(f"No note found with ID: {note_id}")
        conn.close()
        return

    content = note[0]

    # Create a temporary file to edit
    fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
    try:
        with os.fdopen(fd, 'w') as tmp_file:
            tmp_file.write(content)

        # Open the temp file with micro
        subprocess.run(['micro', tmp_path])

        # Read the updated content
        with open(tmp_path, 'r') as tmp_file:
            new_content = tmp_file.read()

        # Update the database if content has changed
        if new_content != content:
            cursor.execute("UPDATE notes SET content = ? WHERE id = ?", (new_content, note_id))
            conn.commit()
            print("Note updated successfully.")
        else:
            print("No changes detected.")

    finally:
        os.remove(tmp_path)
        conn.close()


def search_notes(keyword):
    """Searches for notes containing a keyword in the title or content."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name, GROUP_CONCAT(t.name, ', ')
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.title LIKE ? OR n.content LIKE ?
        GROUP BY n.id
        ORDER BY n.timestamp DESC
    """
    params = [f'%{keyword}%', f'%{keyword}%']
    
    cursor.execute(query, params)
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        print(f"No notes found matching '{keyword}'.")
        return

    print(f"Found {len(notes)} note(s) matching '{keyword}':")
    for note in notes:
        note_id, timestamp, title, content, category, tags = note
        print(f"---")
        print(f"ID: {note_id}")
        print(f"Date: {timestamp}")
        print(f"Title: {title}")
        if category:
            print(f"Category: {category}")
        if tags:
            print(f"Tags: {tags}")
        print(f"Body: {content[:100].replace(chr(10), ' ')}...")

def search_by_tag(tag_name):
    """Searches for all notes with a specific tag."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT n.id, n.timestamp, n.title, n.content, c.name, GROUP_CONCAT(t.name, ', ')
        FROM notes n
        LEFT JOIN categories c ON n.category_id = c.id
        LEFT JOIN note_tags nt ON n.id = nt.note_id
        LEFT JOIN tags t ON nt.tag_id = t.id
        WHERE n.id IN (
            SELECT note_id FROM note_tags WHERE tag_id IN (
                SELECT id FROM tags WHERE name = ?
            )
        )
        GROUP BY n.id
        ORDER BY n.timestamp DESC
    """
    
    cursor.execute(query, (tag_name,))
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        print(f"No notes found with tag '{tag_name}'.")
        return
    
    print(f"Found {len(notes)} note(s) with tag '{tag_name}':")
    for note in notes:
        note_id, timestamp, title, content, category, tags = note
        print(f"---")
        print(f"ID: {note_id}")
        print(f"Date: {timestamp}")
        print(f"Title: {title}")
        if category:
            print(f"Category: {category}")
        if tags:
            print(f"Tags: {tags}")
        print(f"Body: {content[:100].replace(chr(10), ' ')}...")


def main():
    """Main function to parse arguments and add, list, view, save, edit or delete notes."""
    setup_database()

    parser = argparse.ArgumentParser(description="A simple command-line note-taking app.")
    parser.add_argument("title", nargs='?', default=None, help="The title of the note (required for new notes).")
    parser.add_argument("--category", "-c", help="The category of the note.")
    parser.add_argument("--tags", help="A comma-separated list of tags.")
    parser.add_argument("-l", "--list", nargs='?', const=True, default=None, help="List last 10 notes. Can be followed by a category name to filter.")
    parser.add_argument("-v", "--view", help="View a single note by its UUID.")
    parser.add_argument("-s", "--save", help="Save a note to a Markdown file by its UUID.")
    parser.add_argument("-e", "--edit", help="Edit a note's content by its UUID.")
    parser.add_argument("-d", "--delete", help="Delete a note by its UUID.")
    parser.add_argument("--search", help="Search for a keyword in note titles and content.")
    parser.add_argument("--search-tag", help="Search for notes by a specific tag.")


    args = parser.parse_args()

    # Search by keyword
    if args.search:
        search_notes(args.search)
        return

    # Search by tag
    if args.search_tag:
        search_by_tag(args.search_tag)
        return

    # Edit a note
    if args.edit:
        edit_note(args.edit)
        return

    # Delete a note
    if args.delete:
        delete_note(args.delete)
        return

    # Save a note
    if args.save:
        save_note_as_markdown(args.save)
        return

    # View a specific note
    if args.view:
        view_note(args.view)
        return

    # List notes
    if args.list is not None:
        if isinstance(args.list, str):
            list_notes(category_name=args.list)
        else:
            list_notes()
        return

    # Create a new note
    if not args.title:
        if not any([args.list, args.view, args.save, args.edit, args.delete, args.search, args.search_tag]):
             parser.error("A title is required to create a new note.")
        return

    # Get content from micro editor
    fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
    try:
        subprocess.run(['micro', tmp_path])
        with open(tmp_path, 'r') as tmp_file:
            content = tmp_file.read()
    finally:
        os.remove(tmp_path)

    if not content.strip():
        print("Note content is empty. Discarding.")
        sys.exit(0)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    category_name = args.category
    if not category_name:
        category_name = prompt_for_category(cursor)

    tags_str = args.tags
    if not tags_str:
        tags_str = prompt_for_tags()
    
    conn.close()

    add_note(args.title, content, category_name, tags_str)
    print(f"\nNote '{args.title}' added successfully.")

if __name__ == "__main__":
    main()

