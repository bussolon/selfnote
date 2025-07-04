# SelfNote

A lightweight note-taking application for developers and writers to capture, categorize, tag, and search their ideas from either a fast command-line interface or a clean web UI.

## Features

SelfNote is built on a robust backend with two distinct, feature-rich interfaces.

### Core Functionality

*   **SQLite Backend:** All notes are stored in a simple, single-file SQLite database (`notes.db`).
*   **Rich Metadata:** Each note includes a title, content, category, and multiple tags.
*   **Unique IDs:** Notes are identified by UUIDs, ensuring portability and scalability.
*   **Markdown-Friendly:** Note content is treated as Markdown, allowing for rich text formatting.

### Command-Line Interface (CLI)

The CLI is designed for speed and power, allowing you to manage your notes without leaving the terminal.

*   **Full CRUD:** Create, view, edit, and delete notes.
*   **External Editor Integration:** Create and edit notes in your favorite terminal editor (`micro` by default).
*   **Powerful Listing:** List the latest notes, or filter the list by category.
*   **Advanced Search:**
    *   Full-text search across all note titles and content.
    *   Filter notes by a specific tag.
*   **Markdown Export:** Save any note to a portable Markdown file with a Pandoc-compatible YAML frontmatter header.
*   **Interactive Prompts:** Smart prompts guide you to select existing categories or create new ones on the fly.

### Web Interface

The web UI provides a clean, convenient, and visually accessible way to manage your notes.

*   **Full CRUD:** A complete web interface for creating, reading, updating, and deleting notes.
*   **Responsive Layout:** A clean and simple interface that works on different screen sizes.
*   **Full-Text Search:** A search bar in the navigation allows you to find notes from any page.
*   **Category Suggestions:** The category field suggests existing categories as you type, helping maintain consistency.
*   **Pug Templating:** Built with the Pug templating engine for clean and maintainable views.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/bussolon/selfnote.git
    cd selfnote
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Usage

SelfNote can be run as either a command-line tool or a web application.

### Command-Line Interface

The CLI is the primary way to interact with your notes from the terminal.

**Run the CLI:**
```bash
python -m note_app [COMMAND]
```

**Examples:**
```bash
# Create a new note
python -m note_app "My New Note Title" --category "Ideas" --tags "python,project"

# List the 10 most recent notes
python -m note_app -l

# List notes in a specific category
python -m note_app -l "Ideas"

# View a specific note
python -m note_app -v <UUID>

# Edit a note
python -m note_app -e <UUID>

# Delete a note
python -m note_app -d <UUID>

# Full-text search
python -m note_app --search "keyword"

# Search by tag
python -m note_app --search-tag "python"
```

### Web Interface

The web interface provides a graphical way to manage your notes.

**Run the web server:**
```bash
python -m note_app web
```
Then, open your browser and navigate to `http://127.0.0.1:5000`.

## Future Enhancements

We have several ideas for future versions of SelfNote:

*   **Styling Improvements:** Refine the existing CSS to create a more polished and consistent user interface.
*   **User Authentication:** Add an optional login system to the web interface to keep notes private.
