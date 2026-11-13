"""
Shared setup for the experiment scripts.

Import this module *before* ``core`` so that the repository root is on ``sys.path`` and
output paths are independent of the directory the script is launched from.

Set the ``TRIPARTITE_RESULTS_DIR`` environment variable to redirect outputs (used by the tests).
"""
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless-safe: scripts only save figures, they never open windows

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS_DIR = Path(os.environ.get("TRIPARTITE_RESULTS_DIR", ROOT / "results"))
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def result_path(filename):
    """Absolute path for an output file inside the results directory."""
    return RESULTS_DIR / filename
