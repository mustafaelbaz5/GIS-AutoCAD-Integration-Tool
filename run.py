"""Dev entry point for the IDE "Run" button.

Running `src/main.py` directly fails with `ModuleNotFoundError: No
module named 'src'`, because executing a file puts that file's own
folder (`src/`) on `sys.path` rather than the project root, so the
`from src...` imports can't resolve.

This wrapper lives at the project root, so running it (the top-right
Run button, or `python run.py`) puts the root on `sys.path` and the
imports work. On the command line, `python -m src.main` does the same
thing.
"""

from src.main import main

if __name__ == "__main__":
    main()
