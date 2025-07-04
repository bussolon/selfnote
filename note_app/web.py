
from flask import Flask, render_template, request, redirect, url_for
from . import database

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

    @app.route('/')
    def index():
        """Renders the home page with a list of recent notes."""
        notes = database.list_notes()
        return render_template('index.pug', notes=notes, title="All Notes")

    @app.route('/new', methods=['GET', 'POST'])
    def new_note():
        """Handles creation of a new note."""
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            category = request.form.get('category')
            tags = request.form.get('tags')

            if not title or not content:
                # Add some basic validation/error handling
                return "Title and content are required.", 400

            note_id = database.add_note(title, content, category, tags)
            return redirect(url_for('view_note', note_id=note_id))
        
        # For a GET request, show the form
        categories = database.get_all_categories()
        return render_template('new_note.pug', title="New Note", categories=categories)

    @app.route('/edit/<uuid:note_id>', methods=['GET', 'POST'])
    def edit_note(note_id):
        """Handles editing an existing note."""
        note_id_str = str(note_id)
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            category = request.form.get('category')
            tags = request.form.get('tags')

            if not title or not content:
                return "Title and content are required.", 400

            database.update_note(note_id_str, title, content, category, tags)
            return redirect(url_for('view_note', note_id=note_id_str))

        # For a GET request, show the pre-filled form
        note = database.get_note(note_id_str)
        if note:
            categories = database.get_all_categories()
            return render_template('edit_note.pug', note=note, categories=categories, title=f"Edit: {note['title']}")
        else:
            return "Note not found", 404

    @app.route('/search')
    def search():
        """Displays search results."""
        query = request.args.get('q', '')
        if not query:
            return redirect(url_for('index'))
        
        notes = database.search_notes(query)
        return render_template('search_results.pug', notes=notes, query=query, title=f"Search Results for '{query}'")

    @app.route('/delete/<uuid:note_id>', methods=['POST'])
    def delete_note_route(note_id):
        """Handles deleting a note."""
        note_id_str = str(note_id)
        note = database.get_note(note_id_str)
        if note:
            database.delete_note(note_id_str)
        return redirect(url_for('index'))

    @app.route('/note/<uuid:note_id>')
    def view_note(note_id):
        """Renders the page for a single note."""
        note = database.get_note(str(note_id))
        if note:
            return render_template('note.pug', note=note, title=note['title'])
        else:
            return "Note not found", 404
    return app

def run_app():
    """Runs the Flask development server."""
    app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    run_app()
