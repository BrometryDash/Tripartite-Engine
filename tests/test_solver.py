"""Unit and regression tests for core/solver.py."""
import warnings

import numpy as np
import pytest

from core.solver import (
    STATE_NAMES,
    bold_signal,
    get_baseline_parameters,
    hemodynamic_derivatives,
    run_simulation,
    validate_simulation,
)


@pytest.fixture(scope="module")
def params():
    return get_baseline_parameters()


@pytest.fixture(scope="module")
def baseline(params):
    """Baseline 20 Hz, 2 s pulse; long window so the BOLD peak is fully captured."""
    t, y, bold, valid = run_simulation(params, stim_freq=20.0, t_span=(0, 40), method="RK45")
    return {"t": t, "y": dict(zip(STATE_NAMES, y)), "bold": bold, "valid": valid}


# ---------------------------------------------------------------- parameters
def test_baseline_parameters_complete_and_positive(params):
    expected = {"tau_rec", "U", "rho", "V_max", "K_m", "K_G", "k_prod", "k_deg", "J_max", "K_I",
                "tau_Ca", "epsilon", "kappa", "gamma", "tau_0", "alpha", "E_0"}
    assert set(params) == expected
    assert all(v > 0 for v in params.values())
    assert 0 < params["U"] <= 1 and 0 < params["alpha"] < 1 and 0 < params["E_0"] < 1


# ---------------------------------------------------------------- equilibrium / consistency
def test_zero_stimulus_is_an_equilibrium(params):
    _, y, bold, valid = run_simulation(params, stim_freq=0.0, t_span=(0, 20), method="RK45")
    y0 = np.array([1, 0, 0, 0, 0, 1, 1, 1], dtype=float)
    assert valid
    assert np.max(np.abs(y - y0[:, None])) < 1e-6
    assert np.max(np.abs(bold)) < 1e-6


def test_hemodynamic_rest_state_is_a_fixed_point(params):
    derivs = hemodynamic_derivatives(C=0.0, s=0.0, f=1.0, v=1.0, q=1.0, params=params)
    assert np.allclose(derivs, 0.0, atol=1e-12)


def test_bold_is_zero_at_rest(params):
    assert bold_signal(q=1.0, v=1.0, params=params) == pytest.approx(0.0, abs=1e-12)


def test_rk45_and_radau_agree(params):
    _, _, bold_rk, _ = run_simulation(params, stim_freq=20.0, method="RK45")
    _, _, bold_ra, _ = run_simulation(params, stim_freq=20.0, method="Radau")
    assert np.max(np.abs(bold_rk - bold_ra)) < 1e-2  # observed ~1.6e-4 (% BOLD)


def test_states_stay_physical(baseline):
    assert baseline["valid"]
    y = baseline["y"]
    assert y["V"].min() >= -1e-3 and y["V"].max() <= 1.0 + 1e-6
    for name in ("G", "I", "C", "f", "v"):
        assert y[name].min() >= -1e-3, name


def test_short_pulse_is_not_skipped_by_the_adaptive_solver(params):
    """Regression for the max_step fix: a 50 ms pulse must still drive the system."""
    for method in ("RK45", "Radau"):
        _, y, _, _ = run_simulation(params, stim_freq=20.0, stim_start=3.0, stim_end=3.05,
                                    t_span=(0, 10), method=method)
        assert y[1].max() > 10.0, method       # glutamate released
        assert y[0].min() < 0.99, method       # vesicles depleted


def test_validate_simulation_flags_negative_states():
    good = np.array([[1.0], [0.0], [0.0], [0.0], [0.0], [1.0], [1.0], [1.0]])
    bad = good.copy()
    bad[3] = -0.5  # negative calcium
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert validate_simulation(good) is True
    with pytest.warns(UserWarning):
        assert validate_simulation(bad) is False


# ---------------------------------------------------------------- golden values (baseline 20 Hz)
def test_baseline_golden_values(baseline):
    t, y, bold = baseline["t"], baseline["y"], baseline["bold"]
    assert bold.max() == pytest.approx(1.9798, abs=0.01)
    assert y["C"].max() == pytest.approx(0.8397, abs=0.005)
    assert y["V"].min() == pytest.approx(0.1351, abs=0.002)
    assert y["G"].max() == pytest.approx(632.3, abs=3.0)
    assert (y["f"].max() - 1.0) * 100 == pytest.approx(20.98, abs=0.2)
    assert t[np.argmax(bold)] - 3.0 == pytest.approx(12.2, abs=0.3)  # BOLD time-to-peak after onset


# ---------------------------------------------------------------- qualitative model behaviour
def test_peak_bold_is_non_decreasing_with_firing_rate(params):
    peaks = [run_simulation(params, stim_freq=f, t_span=(0, 30), method="RK45")[2].max()
             for f in (1, 5, 10, 20, 40, 80)]
    assert all(b >= a - 1e-9 for a, b in zip(peaks, peaks[1:]))


def test_vesicle_depletion_deepens_with_firing_rate(params):
    minima = [run_simulation(params, stim_freq=f, t_span=(0, 10), method="RK45")[1][0].min()
              for f in (5, 20, 80)]
    assert minima[0] > minima[1] > minima[2]


def test_reduced_uptake_prolongs_glutamate_exposure(params):
    """Core claim of Exp 2: lowering V_max raises glutamate AUC (window long enough to clear)."""
    aucs = []
    for frac in (1.0, 0.5, 0.25):
        q = dict(params, V_max=params["V_max"] * frac)
        t, y, _, _ = run_simulation(q, stim_freq=20.0, t_span=(0, 240), method="RK45")
        aucs.append(np.trapezoid(y[1], x=t))
    assert aucs[0] < aucs[1] < aucs[2]


def test_glutamate_pool_is_cleared_within_the_exp2_window(params):
    """Guards the Exp 2 truncation bug: at 10% uptake the pool must be ~empty at the end of the window."""
    q = dict(params, V_max=params["V_max"] * 0.10)
    _, y, _, _ = run_simulation(q, stim_freq=20.0, t_span=(0, 240), method="RK45")
    assert y[1][-1] < 1.0
