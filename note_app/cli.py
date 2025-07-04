
import argparse
import sys
import os
import subprocess
import tempfile
import re
from datetime import datetime
from . import database

def main():
    """Main function for the CLI."""
    database.setup_database()

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

    # --- Action Handling ---

    if args.search:
        notes = database.search_notes(args.search)
        _display_note_list(notes, f"Found {len(notes)} note(s) matching '{args.search}':")
        return

    if args.search_tag:
        notes = database.search_by_tag(args.search_tag)
        _display_note_list(notes, f"Found {len(notes)} note(s) with tag '{args.search_tag}':")
        return

    if args.edit:
        _edit_note_handler(args.edit)
        return

    if args.delete:
        _delete_note_handler(args.delete)
        return

    if args.save:
        _save_note_handler(args.save)
        return

    if args.view:
        note = database.get_note(args.view)
        _display_full_note(note)
        return

    if args.list is not None:
        category = args.list if isinstance(args.list, str) else None
        notes = database.list_notes(category_name=category)
        _display_note_list(notes)
        return

    # --- Default Action: Create a new note ---
    if not args.title:
        if not any([args.list, args.view, args.save, args.edit, args.delete, args.search, args.search_tag]):
             parser.error("A title is required to create a new note.")
        return
    
    _create_note_handler(args)


# --- Helper Functions for CLI Output and Interaction ---

def _display_note_list(notes, header=""):
    if header:
        print(header)
    if not notes:
        print("No notes found.")
        return
    for note in notes:
        print("---")
        print(f"ID: {note['id']}")
        print(f"Date: {note['timestamp']}")
        print(f"Title: {note['title']}")
        if note.get('category'):
            print(f"Category: {note['category']}")
        if note.get('tags'):
            print(f"Tags: {note['tags']}")
        # Truncate body for list view
        body_preview = note['content'][:100].replace(chr(10), ' ')
        print(f"Body: {body_preview}...")

def _display_full_note(note):
    if not note:
        print("Note not found.")
        return
    print("---")
    print(f"Title: {note['title']}")
    print(f"Date: {note['timestamp']}")
    if note.get('category'):
        print(f"Category: {note['category']}")
    if note.get('tags'):
        print(f"Tags: {note['tags']}")
    print(f"---\n{note['content']}")

def _create_note_handler(args):
    """Handles the logic for creating a new note."""
    content = _get_content_from_editor()
    if not content.strip():
        print("Note content is empty. Discarding.")
        return

    category_name = args.category or _prompt_for_category()
    tags_str = args.tags or _prompt_for_tags()

    note_id = database.add_note(args.title, content, category_name, tags_str)
    print(f"\nNote '{args.title}' (ID: {note_id}) added successfully.")

def _edit_note_handler(note_id):
    """Handles the logic for editing a note."""
    note = database.get_note(note_id)
    if not note:
        print(f"No note found with ID: {note_id}")
        return
    
    new_content = _get_content_from_editor(initial_content=note['content'])
    
    if new_content != note['content']:
        database.update_note_content(note_id, new_content)
        print("Note updated successfully.")
    else:
        print("No changes detected.")

def _delete_note_handler(note_id):
    """Handles the logic for deleting a note."""
    note = database.get_note(note_id)
    if not note:
        print(f"No note found with ID: {note_id}")
        return
    
    confirm = input(f'Are you sure you want to delete "{note["title"]}"? [y/N]: ')
    if confirm.lower() == 'y':
        database.delete_note(note_id)
        print(f'Note "{note["title"]}" has been deleted.')
    else:
        print("Deletion cancelled.")

def _save_note_handler(note_id):
    """Handles the logic for saving a note to a markdown file."""
    note = database.get_note(note_id)
    if not note:
        print(f"No note found with ID: {note_id}")
        return

    safe_title = re.sub(r'[^\w\s-]', '', note['title']).strip().lower()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    date_obj = datetime.strptime(note['timestamp'], '%Y-%m-%d %H:%M:%S')
    filename = f"{date_obj.strftime('%Y_%m_%d')}_{safe_title}.md"

    yaml_header = "---\n"
    yaml_header += f"uuid: {note['id']}\n"
    yaml_header += f"title: \"{note['title']}\"\n"
    if note.get('category'):
        yaml_header += f"category: {note['category']}\n"
    if note.get('tags'):
        tags_list = [tag.strip() for tag in note['tags'].split(',')]
        yaml_header += "tags:\n"
        for tag in tags_list:
            yaml_header += f"  - {tag}\n"
    yaml_header += "---\n\n"

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(yaml_header)
            f.write(note['content'])
        print(f"Note successfully saved to: {filename}")
    except IOError as e:
        print(f"Error saving file: {e}")

def _get_content_from_editor(initial_content=""):
    """Opens micro to get note content."""
    fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
    try:
        with os.fdopen(fd, 'w') as tmp_file:
            tmp_file.write(initial_content)
        
        subprocess.run(['micro', tmp_path])

        with open(tmp_path, 'r') as tmp_file:
            return tmp_file.read()
    finally:
        os.remove(tmp_path)

def _prompt_for_category():
    """Prompts the user to select or create a category."""
    print("\n--- Select a Category ---")
    categories = database.get_all_categories()
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
        print("Invalid choice. Please try again.")

def _prompt_for_tags():
    """Prompts the user for optional tags."""
    print("\n--- Add Tags (Optional) ---")
    return input("Enter comma-separated tags, or press Enter to skip: ")

if __name__ == '__main__':
    main()
