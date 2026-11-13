#!/usr/bin/env python3
"""
Run every experiment and regenerate everything in ``results/``.

    python run_all.py              # all experiments (~45 s)
    python run_all.py exp_1 exp_7  # only experiments whose file name starts with these prefixes
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENTS = [
    "exp_0_verification",
    "exp_1_frequency",
    "exp_2_tboa",
    "exp_3_vascular",
    "exp_4_sensitivity",
    "exp_5_uncertainty",
    "exp_6_plausibility",
    "exp_7_temporal_bottleneck",
    "exp_8_astrocyte_oat",
    "exp_9_hemo_isolation",
    "exp_diagnostic",
]


def main(selection):
    chosen = [e for e in EXPERIMENTS if not selection or any(e.startswith(s) for s in selection)]
    if not chosen:
        sys.exit(f"No experiment matches {selection}. Available: {', '.join(EXPERIMENTS)}")

    failed = []
    for name in chosen:
        start = time.time()
        proc = subprocess.run([sys.executable, str(ROOT / "experiments" / f"{name}.py")],
                              capture_output=True, text=True)
        status = "ok" if proc.returncode == 0 else "FAILED"
        print(f"{name:<28} {status:<7} {time.time() - start:5.1f}s")
        if proc.returncode != 0:
            failed.append(name)
            print(proc.stderr[-2000:])
    if failed:
        sys.exit(f"\n{len(failed)} experiment(s) failed: {', '.join(failed)}")
    print(f"\nAll {len(chosen)} experiments finished. Outputs are in {ROOT / 'results'}")


if __name__ == "__main__":
    main(sys.argv[1:])
