import sys
from . import web

def main():
    """
    Acts as a dispatcher, running either the CLI or the web app
    based on the command-line arguments.
    """
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        # Create the Flask app using the factory
        app = web.create_app()
        # Run the app in debug mode for development
        app.run(debug=True, port=5001)
    else:
        from . import cli
        cli.main()

if __name__ == '__main__':
    main()