# SelfNote

A lightweight note-taking application for developers and writers to capture, categorize, tag, and search their ideas from either a fast command-line interface or a clean web UI.

## Features

SelfNote is built on a robust backend with two distinct, feature-rich interfaces.

### Core Functionality

*   **Multi-User Support:** A full user authentication system allows multiple users to register and manage their own private set of notes.
*   **Secure Passwords:** User passwords are never stored in plain text. They are securely hashed and salted using modern standards.
*   **SQLite Backend:** All notes are stored in a simple, single-file SQLite database (`notes.db`).
*   **Rich Metadata:** Each note includes a title, content, category, and multiple tags.
*   **Markdown-Friendly:** Note content is treated as Markdown, allowing for rich text formatting.

### Command-Line Interface (CLI)

The CLI is designed for speed and power, allowing you to manage notes for any user without leaving the terminal.

*   **User-Context Aware:** All commands are performed on behalf of a specific user, specified via the `--username` flag or a `SELFNOTE_USER` environment variable.
*   **Full CRUD:** Create, view, edit, and delete notes for the specified user.
*   **External Editor Integration:** Create and edit notes in your favorite terminal editor (`micro` by default).
*   **Powerful Listing & Search:** List, filter, and search notes belonging to the specified user.
*   **Markdown Export:** Save any note to a portable Markdown file with a Pandoc-compatible YAML frontmatter header.

### Web Interface

The web UI provides a clean, secure, and visually accessible way to manage your notes.

*   **Full Authentication Flow:** Users can register, log in, and log out. All note-related pages are protected and require a login.
*   **Full CRUD:** A complete web interface for creating, reading, updating, and deleting your own notes.
*   **Responsive Layout:** A clean and simple interface that works on different screen sizes.
*   **Full-Text & Tag Search:** A search bar and clickable tags allow for easy discovery of your notes.
*   **Category Suggestions:** The category field suggests your existing categories as you type.

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

### Web Interface (Recommended for most users)

The web interface is the primary way to interact with SelfNote.

**Run the web server:**
```bash
python -m note_app web
```
Then, open your browser and navigate to `http://127.0.0.1:5000`. You will need to register a new user before you can log in and start creating notes.

### Command-Line Interface (Admin & Power-User Tool)

The CLI acts as a trusted admin tool for your local database. You must specify which user you are acting on behalf of.

**Set the user for your session (optional):**
```bash
export SELFNOTE_USER=your_username
```

**Run commands:**
```bash
# Create a new note for the specified user
python -m note_app "My New Note Title" --username your_username

# List notes for the user set in the environment variable
python -m note_app -l

# View a note for a different user
python -m note_app -v <UUID> --username another_user
```

## Future Enhancements

We have several ideas for future versions of SelfNote:

*   **Styling Improvements:** Refine the existing CSS to create a more polished and consistent user interface.
