# From Idea to Application: Building a CLI Note-Taking Tool

This document summarizes the collaborative development of a command-line note-taking application. The project started with a simple goal and evolved through iterative feature additions into a robust and user-friendly tool.

## The Initial Spark

The initial idea was to create a simple Python program to encourage more frequent writing by making it easy to capture small, categorized notes from the command line.

## Core Requirements

We established a solid foundation by deciding on the following core requirements:
-   **Database Storage:** Notes would be stored in an SQLite database (`notes.db`).
-   **Rich Metadata:** Each note would have a title, content, a category, and multiple tags.
-   **Robust IDs:** We opted to use UUIDs for all primary keys to ensure future scalability.
-   **Timestamps:** Every note would be automatically timestamped upon creation.

## The Evolutionary Development Process

We built the application feature by feature, refining the user experience at each step.

### 1. Basic Note Creation
The first version allowed creating a note by passing all its data as command-line arguments.

### 2. Interactive Content and Metadata
We quickly realized that writing multiline notes as an argument was impractical. We pivoted to a more interactive approach:
-   **Multiline Body:** The script was modified to read multiline content from standard input, finishing with `Ctrl+D`.
-   **Interactive Prompts:** If the category or tags were not provided as arguments, the script would prompt the user for them. For categories, it would list existing ones to choose from or allow the creation of a new one.

### 3. Viewing and Listing Notes
To make the tool useful, we added ways to retrieve the notes:
-   **List Recent Notes (`-l`):** A flag to list the 10 most recent notes, showing a preview of their content and metadata.
-   **Filter by Category (`-l <category>`):** The list function was enhanced to filter by a specific category.
-   **View Full Note (`-v <uuid>`):** A flag to view the complete content of a single note.

### 4. A Consistent Editor Experience with `micro`
To improve the writing experience, we integrated the `micro` text editor:
-   **Editing Notes (`-e <uuid>`):** We added an edit feature that opens the note's content in `micro`.
-   **Creating Notes:** We replaced the `Ctrl+D` input method with `micro`, making the creation and editing workflows identical and more powerful.

### 5. Advanced Search
To handle a growing collection of notes, we implemented two search methods:
-   **Full-Text Search (`--search <keyword>`):** Searches for a keyword across the titles and content of all notes.
-   **Tag-Based Search (`--search-tag <tag>`):** Lists all notes associated with a specific tag.

### 6. Data Management and Portability
Finally, we added crucial management features:
-   **Deleting Notes (`-d <uuid>`):** A command to delete a note, with a confirmation prompt to prevent accidents.
-   **Markdown Export (`-s <uuid>`):** A feature to save a note as a portable Markdown file, complete with a Pandoc-compatible YAML frontmatter header containing all its metadata.

## Final Outcome

The result of our collaboration is `note.py`, a feature-rich, command-line note-taking application that is both powerful for advanced users and simple enough for quick, everyday use. It supports creating, viewing, listing, editing, deleting, searching, and exporting notes in a structured and user-friendly way.

## Phase 2: Adding a Flask Web Interface

Building on the solid foundation of the CLI tool, we evolved the project into a dual-interface application by adding a web UI powered by Flask.

### 1. Project Restructuring
The most critical step was a complete architectural refactoring to ensure the CLI and web app could coexist and share logic.
-   **Code Separation:** We created a `note_app` Python package. The original script's logic was split into a `database.py` file (the data layer) and a `cli.py` file (the CLI presentation layer).
-   **Single Entry Point:** We introduced a `__main__.py` dispatcher, allowing the application to be run as a package (`python -m note_app`). This dispatcher launches the CLI by default, or the web app if run with the `web` argument (`python -m note_app web`).
-   **Version Control:** We initialized a Git repository and created a `.gitignore` file to properly manage the project's source code.

### 2. Building the Web Application
With the backend logic cleanly separated, we built the web interface step-by-step.
-   **Dependencies:** We chose `Flask` as the web framework and `pypugjs` to enable the use of the Pug templating engine, as requested.
-   **Core Functionality (CRUD):** We implemented the full set of Create, Read, Update, and Delete operations:
    -   **Read:** The home page (`/`) lists all recent notes, with links to view each one on its own dedicated page (`/note/<uuid>`).
    -   **Create:** A `/new` page provides a form for creating new notes.
    -   **Update:** An `/edit/<uuid>` page allows for modifying a note's title, content, category, and tags.
    -   **Delete:** A "Delete" button on the edit page provides a safe, confirmation-based way to remove notes.
-   **Templating:** We used a `page.pug` base template to ensure a consistent layout and navigation across the entire web application, extending it for the index, view, new, and edit pages.

The final result is a powerful and maintainable application with two distinct, fully-featured interfaces sharing a single, robust backend.
