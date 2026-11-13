"""Smoke tests: every experiment runs end-to-end and writes its expected outputs (to a temp dir)."""
import importlib
import os
from pathlib import Path

import pytest

RESULTS = Path(os.environ["TRIPARTITE_RESULTS_DIR"])

# module name, callable, kwargs, expected output files
CASES = [
    ("exp_0_verification", "run_experiment", {}, ["exp_0_verification.png"]),
    ("exp_1_frequency", "run_frequency_sweep", {}, ["exp_1_frequency_response.csv", "exp_1_frequency_response.png"]),
    ("exp_2_tboa", "run_tboa_experiment", {}, ["exp_2_tboa_response.csv", "exp_2_tboa_response.png"]),
    ("exp_3_vascular", "run_vascular_experiment", {}, ["exp_3_vascular_impairment.csv", "exp_3_vascular_impairment.png"]),
    ("exp_4_sensitivity", "run_sensitivity", {}, ["exp_4_sensitivity.csv", "exp_4_sensitivity.png"]),
    ("exp_5_uncertainty", "run_uncertainty_propagation", {"n_simulations": 5},
     ["exp_5_uncertainty.csv", "exp_5_uncertainty_summary.json", "exp_5_uncertainty.png"]),
    ("exp_6_plausibility", "run_plausibility_check", {}, ["exp_6_plausibility.csv", "exp_6_plausibility.png"]),
    ("exp_7_temporal_bottleneck", "run_temporal_bottleneck_analysis", {},
     ["exp_7_temporal_bottleneck.csv", "exp_7_temporal_bottleneck.png"]),
    ("exp_8_astrocyte_oat", "run_astrocyte_temporal_oat", {}, ["exp_8_astrocyte_oat.csv", "exp_8_astrocyte_oat.png"]),
    ("exp_9_hemo_isolation", "run_hemo_isolation", {}, ["exp_9_hemo_isolation.png"]),
    ("exp_diagnostic", "run_diagnostic", {}, ["diagnostic_chain.csv", "diagnostic_chain.png"]),
]


@pytest.mark.parametrize("module, func, kwargs, outputs", CASES, ids=[c[0] for c in CASES])
def test_experiment_runs_and_writes_outputs(module, func, kwargs, outputs):
    getattr(importlib.import_module(module), func)(**kwargs)
    for name in outputs:
        assert (RESULTS / name).stat().st_size > 0, name


def test_exp2_reports_duration_and_untruncated_auc():
    """
    Exp 2 guards: (1) the integration window must let the glutamate pool clear, otherwise the AUC at low
    uptake capacity is badly underestimated (it was 2.9x instead of ~11x the baseline AUC);
    (2) TBOA prolongs the BOLD response (FWHM) without delaying its onset (T50).
    """
    import pandas as pd
    df = pd.read_csv(RESULTS / "exp_2_tboa_response.csv")  # rows ordered 100% -> 10% EAAT capacity
    assert df["Glutamate_AUC_uMs"].iloc[-1] > 8 * df["Glutamate_AUC_uMs"].iloc[0]
    assert df["BOLD_T50_rise_s"].max() - df["BOLD_T50_rise_s"].min() < 0.5
    assert df["BOLD_FWHM_s"].is_monotonic_increasing
    assert df["BOLD_FWHM_s"].iloc[-1] > 5 * df["BOLD_FWHM_s"].iloc[0]


def test_exp8_upstream_glutamate_parameters_beat_astrocyte_parameters():
    """README 3.8: glutamate-pool parameters shorten the Ca2+ delay more than any astrocytic parameter."""
    import pandas as pd
    df = pd.read_csv(RESULTS / "exp_8_astrocyte_oat.csv").set_index("Parameter")
    astro = df[df["Module"] == "astrocyte"]["TTP_Reduction_s"].max()
    pool = df[df["Module"] == "glutamate pool"]["TTP_Reduction_s"].min()
    assert pool > astro


def test_exp5_summary_contains_timing_spread():
    import json
    summary = json.loads((RESULTS / "exp_5_uncertainty_summary.json").read_text())
    for key in ("BOLD_TTP_min_s", "BOLD_TTP_median_s", "BOLD_TTP_max_s"):
        assert key in summary
    assert summary["BOLD_TTP_min_s"] <= summary["BOLD_TTP_median_s"] <= summary["BOLD_TTP_max_s"]
