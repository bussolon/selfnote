
from flask import Flask, render_template, request, redirect, url_for, session, flash
from . import database
import markdown
import os
from functools import wraps

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

    @app.template_filter('markdown')
    def markdown_filter(s):
        return markdown.markdown(s)

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            if not username or not email or not password:
                flash("All fields are required.", "error")
                return redirect(url_for('register'))

            user_id = database.create_user(username, email, password)
            if user_id:
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
            else:
                flash("Username or email already exists.", "error")
                return redirect(url_for('register'))
        return render_template('register.pug', title="Register")

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = database.verify_password(username, password)
            if user:
                session['user_id'] = user['id']
                session['username'] = user['username']
                return redirect(url_for('index'))
            else:
                flash("Invalid username or password.", "error")
                return redirect(url_for('login'))
        return render_template('login.pug', title="Login")

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))

    @app.route('/')
    @login_required
    def index():
        """Renders the home page with a list of recent notes."""
        notes = database.list_notes(session['user_id'])
        return render_template('index.pug', notes=notes, title="All Notes")

    @app.route('/new', methods=['GET', 'POST'])
    @login_required
    def new_note():
        """Handles creation of a new note."""
        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            category = request.form.get('category')
            tags = request.form.get('tags')

            if not title or not content:
                flash("Title and content are required.", "error")
                return redirect(url_for('new_note'))

            note_id = database.add_note(title, content, category, tags, session['user_id'])
            return redirect(url_for('view_note', note_id=note_id))
        
        categories = database.get_all_categories(session['user_id'])
        return render_template('new_note.pug', title="New Note", categories=categories)

    @app.route('/edit/<uuid:note_id>', methods=['GET', 'POST'])
    @login_required
    def edit_note(note_id):
        """Handles editing an existing note."""
        note_id_str = str(note_id)
        note = database.get_note(note_id_str, session['user_id'])
        if not note:
            return "Note not found or you don't have permission to edit it.", 404

        if request.method == 'POST':
            title = request.form['title']
            content = request.form['content']
            category = request.form.get('category')
            tags = request.form.get('tags')

            if not title or not content:
                flash("Title and content are required.", "error")
                return redirect(url_for('edit_note', note_id=note_id_str))

            database.update_note(note_id_str, title, content, category, tags, session['user_id'])
            return redirect(url_for('view_note', note_id=note_id_str))

        categories = database.get_all_categories(session['user_id'])
        return render_template('edit_note.pug', note=note, categories=categories, title=f"Edit: {note['title']}")

    @app.route('/search')
    @login_required
    def search():
        """Displays search results."""
        query = request.args.get('q', '')
        if not query:
            return redirect(url_for('index'))
        
        notes = database.search_notes(query, session['user_id'])
        return render_template('search_results.pug', notes=notes, query=query, title=f"Search Results for '{query}'")

    @app.route('/delete/<uuid:note_id>', methods=['POST'])
    @login_required
    def delete_note_route(note_id):
        """Handles deleting a note."""
        note_id_str = str(note_id)
        # The get_note function ensures the user owns the note.
        note = database.get_note(note_id_str, session['user_id'])
        if note:
            database.delete_note(note_id_str, session['user_id'])
        return redirect(url_for('index'))

    @app.route('/tag/<tag_name>')
    @login_required
    def view_by_tag(tag_name):
        """Displays all notes with a specific tag."""
        notes = database.search_by_tag(tag_name, session['user_id'])
        return render_template('search_results.pug', notes=notes, query=f"tag: {tag_name}", title=f"Notes tagged with '{tag_name}'")

    @app.route('/note/<uuid:note_id>')
    @login_required
    def view_note(note_id):
        """Renders the page for a single note."""
        note = database.get_note(str(note_id), session['user_id'])
        if note:
            return render_template('note.pug', note=note, title=note['title'])
        else:
            return "Note not found or you don't have permission to view it.", 404
    return app

def run_app():
    """Runs the Flask development server."""
    app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    run_app()
