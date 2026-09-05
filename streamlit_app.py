"""Root-level entrypoint for Streamlit Cloud deployment.

Streamlit Cloud runs this file from the repository root.
We add src/ to sys.path so that 'smartcsv' package is importable,
then delegate to the actual app.
"""

import sys
from pathlib import Path

# Add src/ to path so 'smartcsv' package is importable
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Now delegate to the real app entry point
from smartcsv.app import main  # noqa: E402

main()
