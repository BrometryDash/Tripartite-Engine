"""
Experiment 9: Hemodynamic Intrinsic Delay Analysis
Bypasses the cellular model by feeding a synthetic Ca2+ pulse directly
into the Friston equations to quantify the intrinsic vascular delay.

Uses the same hemodynamic and BOLD functions as the full model (core.solver), so this experiment
always tests exactly the equations used elsewhere.
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

from _common import result_path
from core.solver import bold_signal, get_baseline_parameters, hemodynamic_derivatives


def synthetic_ca(t, peak_time=2.0, width=0.5):
    """Gaussian synthetic Calcium pulse peaking at `peak_time`."""
    return np.exp(-((t - peak_time)**2) / (2 * width**2))


def hemo_odes(t, y, params):
    s, f, v, q = y
    return list(hemodynamic_derivatives(synthetic_ca(t), s, f, v, q, params))


def run_hemo_isolation():
    print("=" * 60)
    print(" 🩸 EXPERIMENT 9: HEMODYNAMIC INTRINSIC DELAY")
    print("=" * 60)

    params = get_baseline_parameters()  # only the hemodynamic entries are used by hemo_odes
    t_span = (0, 20)

    sol = solve_ivp(hemo_odes, t_span, [0.0, 1.0, 1.0, 1.0], args=(params,),
                    t_eval=np.linspace(t_span[0], t_span[1], 2000), method='RK45')

    t = sol.t
    C_trace = synthetic_ca(t)
    bold = bold_signal(q=sol.y[3], v=sol.y[2], params=params)

    ca_peak_time = t[np.argmax(C_trace)]
    bold_peak_time = t[np.argmax(bold)]
    intrinsic_delay = bold_peak_time - ca_peak_time

    print(f" ▸ Synthetic Ca2+ Peak: {ca_peak_time:.2f} s")
    print(f" ▸ Resulting BOLD Peak: {bold_peak_time:.2f} s")
    print(f" ▸ Intrinsic Hemodynamic Delay: {intrinsic_delay:.2f} s")

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(t, C_trace, color='darkorange', linewidth=2, label="Synthetic Ca2+ Input")
    ax1.set_ylabel("Ca2+ (uM)", color='darkorange')
    ax1.tick_params(axis='y', labelcolor='darkorange')

    ax2 = ax1.twinx()
    ax2.plot(t, bold, color='royalblue', linewidth=2, label="Predicted BOLD")
    ax2.set_ylabel("BOLD Signal (%)", color='royalblue')
    ax2.tick_params(axis='y', labelcolor='royalblue')

    ax1.axvline(ca_peak_time, color='darkorange', linestyle='--', alpha=0.5)
    ax2.axvline(bold_peak_time, color='royalblue', linestyle='--', alpha=0.5)

    plt.title(f"Hemodynamic Isolation (Intrinsic Delay = {intrinsic_delay:.2f}s)")
    plt.savefig(result_path('exp_9_hemo_isolation.png'), dpi=200)
    print("✅ Plot saved to results/exp_9_hemo_isolation.png")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_hemo_isolation()
