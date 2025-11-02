from scripts.main import main
import argparse
import sys

if __name__ == "__main__":
    # This is a bit of a hack to make the argparse from utils.config work when called from here.
    # A better solution would be to centralize argument parsing.
    # For now, we need to ensure the required '--email' argument is passed.
    if '--email' not in sys.argv:
        print("Error: the --email argument is required", file=sys.stderr)
        sys.exit(1)

    main()
