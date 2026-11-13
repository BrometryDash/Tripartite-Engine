"""Test configuration: send all experiment outputs to a temporary directory, never to results/."""
import os
import tempfile

# Must be set before any experiment module (which imports experiments/_common.py) is imported.
os.environ.setdefault("TRIPARTITE_RESULTS_DIR", tempfile.mkdtemp(prefix="tripartite_results_"))
os.environ.setdefault("MPLBACKEND", "Agg")
