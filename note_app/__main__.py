
import sys

def main():
    """
    Acts as a dispatcher, running either the CLI or the web app
    based on the command-line arguments.
    """
    # To be able to run the web app later, we check for a 'web' argument.
    # For now, we only have the CLI.
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        try:
            from . import web
            # We will create a 'run_app' function in web.py
            web.run_app()
        except ImportError:
            print("Web application is not yet implemented.")
            sys.exit(1)
    else:
        from . import cli
        # Pass all command-line arguments except the script name itself
        # to the CLI's main function.
        # Note: We'll need to adjust cli.py to handle this if it's not already.
        # For now, let's assume argparse handles it correctly.
        cli.main()

if __name__ == '__main__':
    main()
