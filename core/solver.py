"""
Tripartite-Engine ODE solver.

A reduced, feed-forward mechanistic model linking

    presynaptic vesicle depression (Tsodyks-Markram)  ->  extracellular glutamate pool
    (Michaelis-Menten uptake)  ->  astrocytic IP3 / Ca2+ (phenomenological)
    ->  Friston/Balloon hemodynamics  ->  BOLD signal.

State vector (8 variables, time in seconds)::

    V  fraction of releasable vesicles (dimensionless, 0-1)
    G  extracellular glutamate pool (uM)
    I  astrocytic IP3 (uM)
    C  astrocytic cytosolic Ca2+ (uM)
    s  vasodilatory signal (1/s)
    f  normalised blood flow (1 at rest)
    v  normalised blood volume (1 at rest)
    q  normalised deoxyhaemoglobin content (1 at rest)

See ``docs/MODEL.md`` for the equations and parameter table.
"""
import warnings

import numpy as np
from scipy.integrate import solve_ivp

STATE_NAMES = ("V", "G", "I", "C", "s", "f", "v", "q")

# Lower bound used inside fractional powers so that f, v can never reach 0 (avoids NaN / complex values).
_POSITIVITY_FLOOR = 1e-5

# BOLD observation-model constants. Form: V0 * [k1(1-q) + k2(1-q/v) + k3(1-v)], k1 = 7*E_0, k2 = 2
# (Buxton et al., 2004; Stephan et al., 2007). Note: the literature gives k3 = 2*E_0 - 0.2 (= 0.6 for
# E_0 = 0.4) and V0 = 0.02 (Friston et al., 2000); this code uses k3 = 0.2 and V0 = 0.04. See docs/MODEL.md.
RESTING_BLOOD_VOLUME_FRACTION = 0.04  # V_0
_K2 = 2.0
_K3 = 0.2


def get_baseline_parameters():
    """Return the baseline parameter set (see docs/MODEL.md for meaning and units)."""
    return {
        'tau_rec': 0.8, 'U': 0.4, 'rho': 250.0, 'V_max': 50.0, 'K_m': 15.0,
        'K_G': 10.0, 'k_prod': 0.5, 'k_deg': 2.0, 'J_max': 20.0, 'K_I': 2.0, 'tau_Ca': 3.0,
        'epsilon': 0.1, 'kappa': 0.65, 'gamma': 0.41, 'tau_0': 0.98, 'alpha': 0.33, 'E_0': 0.4
    }


def hemodynamic_derivatives(C, s, f, v, q, params):
    """
    Friston/Balloon hemodynamic block driven by astrocytic Ca2+ ``C``.

    Returns ``(ds_dt, df_dt, dv_dt, dq_dt)``. Shared by the full model and by Experiment 9
    (which drives this block with a synthetic Ca2+ pulse) so the two can never diverge.
    """
    p = params
    ds_dt = p['epsilon'] * C - p['kappa'] * s - p['gamma'] * (f - 1.0)
    df_dt = s

    f_safe = max(f, _POSITIVITY_FLOOR)
    v_safe = max(v, _POSITIVITY_FLOOR)

    dv_dt = (f_safe - v_safe ** (1.0 / p['alpha'])) / p['tau_0']
    E_f = 1.0 - (1.0 - p['E_0']) ** (1.0 / f_safe)  # oxygen extraction fraction
    dq_dt = (f_safe * (E_f / p['E_0']) - q * v_safe ** ((1.0 - p['alpha']) / p['alpha'])) / p['tau_0']
    return ds_dt, df_dt, dv_dt, dq_dt


def bold_signal(q, v, params):
    """Percent BOLD signal change from normalised deoxyhaemoglobin ``q`` and volume ``v``."""
    k1 = 7.0 * params['E_0']
    bold_frac = k1 * (1.0 - q) + _K2 * (1.0 - (q / v)) + _K3 * (1.0 - v)
    return RESTING_BLOOD_VOLUME_FRACTION * bold_frac * 100


def tripartite_odes(t, y, params, stimulus_func):
    V, G, I, C, s, f, v, q = y
    p = params
    R_t = stimulus_func(t)

    # 1. Synapse (Tsodyks-Markram depression & Michaelis-Menten uptake)
    dV_dt = (1.0 - V) / p['tau_rec'] - p['U'] * R_t * V
    dG_dt = p['rho'] * p['U'] * R_t * V - (p['V_max'] * G) / (p['K_m'] + G)

    # 2. Astrocyte (saturating IP3 generation & Ca2+ release)
    dI_dt = p['k_prod'] * (G / (p['K_G'] + G)) - p['k_deg'] * I
    dC_dt = p['J_max'] * (I ** 2 / (I ** 2 + p['K_I'] ** 2)) - (C / p['tau_Ca'])

    # 3. Hemodynamics (Friston-style formulation)
    ds_dt, df_dt, dv_dt, dq_dt = hemodynamic_derivatives(C, s, f, v, q, p)

    return [dV_dt, dG_dt, dI_dt, dC_dt, ds_dt, df_dt, dv_dt, dq_dt]


def validate_simulation(y):
    """Checks for biological impossibility (e.g., negative concentrations)."""
    V, G, I, C, s, f, v, q = y
    tolerance = -1e-3  # Allow minuscule numerical tolerance around zero

    if np.any(V < tolerance) or np.any(G < tolerance) or np.any(I < tolerance) or np.any(C < tolerance):
        warnings.warn("Validation Warning: A cellular state variable dropped below zero.")
        return False
    if np.any(f < tolerance) or np.any(v < tolerance):
        warnings.warn("Validation Warning: Blood flow or volume dropped below zero.")
        return False
    return True


def run_simulation(params, stim_freq=20.0, stim_start=3.0, stim_end=5.0, t_span=(0, 25), method='Radau'):
    """
    Integrate the model for a rectangular presynaptic firing-rate pulse.

    Parameters
    ----------
    params : dict            parameter set (see ``get_baseline_parameters``)
    stim_freq : float        presynaptic firing rate during the pulse (Hz)
    stim_start, stim_end : float   pulse onset / offset (s)
    t_span : (float, float)  integration window (s). Choose it long enough for the BOLD peak:
                             with the baseline parameters the peak is ~12 s after onset and slower
                             parameter sets (e.g. reduced uptake) can peak much later.
    method : str             any ``scipy.integrate.solve_ivp`` method

    Returns
    -------
    t, y, bold, is_valid
        ``t`` (5000 samples), state matrix ``y`` (8 x 5000, ordered as ``STATE_NAMES``),
        percent BOLD change, and ``True`` only if the solver converged *and* all states stayed
        physically non-negative.
    """
    def stimulus(t):
        return stim_freq if stim_start <= t <= stim_end else 0.0

    y0 = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]

    # max_step=0.01 keeps the adaptive solver from stepping over short stimulus pulses.
    sol = solve_ivp(
        fun=tripartite_odes, t_span=t_span, y0=y0, args=(params, stimulus),
        method=method, t_eval=np.linspace(t_span[0], t_span[1], 5000),
        rtol=1e-5, atol=1e-7, max_step=0.01
    )

    is_valid = validate_simulation(sol.y)
    if not sol.success:
        warnings.warn(f"ODE solver did not converge: {sol.message}")
        is_valid = False

    bold = bold_signal(q=sol.y[7], v=sol.y[6], params=params)

    return sol.t, sol.y, bold, is_valid
