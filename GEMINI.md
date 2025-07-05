# Gemini Project Context: SelfNote

This is a summary of the SelfNote project for the Gemini AI assistant.

## 1. Project Goal

A dual-interface (CLI and Web) note-taking application built with Python. It is multi-user, secure, and uses a SQLite database.

## 2. Key Technologies

-   **Backend:** Python, Flask
-   **Frontend/Templating:** Pug (via `pypugjs`)
-   **Database:** SQLite
-   **Testing:** pytest
-   **Dependencies:** Managed in `requirements.txt`

## 3. Project Structure

The core logic is in the `note_app` package.

-   `note_app/database.py`: **Data Layer.** All database interaction logic lives here. Functions are designed to be testable and accept an optional `db_conn` object.
-   `note_app/web.py`: **Web Layer.** The Flask application, routes, and view logic. Uses the "Application Factory" pattern (`create_app`).
-   `note_app/cli.py`: **CLI Layer.** The command-line interface logic.
-   `note_app/__main__.py`: **Dispatcher.** The main entry point (`python -m note_app`). It launches either the web app or the CLI.
-   `note_app/templates/`: Contains all Pug templates.
-   `tests/`: Contains all `pytest` tests.
-   `wsgi.py`: The entry point for the Gunicorn production server.
-   `Dockerfile`: Builds a container image for production deployment.

## 4. Key Commands

-   **Run Web App (Dev):** `python -m note_app web`
-   **Run CLI:** `python -m note_app --username <user> [COMMAND]`
-   **Run Tests:** `PYTHONPATH=. pytest`

## 5. Important Conventions

-   **User Context:** All database functions require a `user_id` to ensure data isolation.
-   **CLI as Admin:** The CLI is a trusted tool and does not handle passwords. It determines the user via `--username` or the `SELFNOTE_USER` environment variable.
-   **Pug Templates:** We use Pug mixins (e.g., in `_helpers.pug`) for repeated template logic like rendering tag lists.

## 6. Collaboration Protocol

This section outlines the best practices for the human-AI collaboration on this project.

**For the Human (The Architect):**
*   **State Clear Goals:** Begin each major task by stating a clear, high-level objective (e.g., "Add user authentication," "Improve the CSS").
*   **Approve the Plan:** Wait for the AI to propose a step-by-step plan. Approve or amend the plan before execution begins.
*   **Test Each Step:** After the AI completes a step, test it immediately.
*   **Provide Specific Feedback:** If an error occurs, provide the full error message. If you have a theory about the cause, state it.
*   **Commit Often:** After a feature is complete and working, instruct the AI to commit the changes to Git.

**For the AI (The Builder):**
*   **Clarify and Plan:** Before writing any code, propose a clear, step-by-step plan to achieve the stated goal.
*   **Execute One Step at a Time:** Do not move on to the next step until the current one is approved and tested.
*   **Explain Critical Commands:** Before running any command that modifies the file system or system state, provide a brief explanation of what it does.
*   **Adhere to Conventions:** Rigorously follow the project's existing style, architecture, and conventions.
*   **Maintain Documentation:** Keep the `README.md` and `selfblog.md` updated as new features are completed.
*   **Prompt for Protocol Adherence:** If the user seems to be deviating from the agreed-upon workflow (e.g., by giving unclear instructions or not testing a step), gently remind them of the protocol to ensure the collaboration remains efficient and effective.
