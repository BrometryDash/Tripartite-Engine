"""
Experiment 0: Numerical Verification
Tests baseline stability, state positivity, and solver convergence.
"""
import time
import numpy as np
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_experiment():
    print("="*50)
    print(" 🧪 EXPERIMENT 0: NUMERICAL VERIFICATION")
    print("="*50)
    
    params = get_baseline_parameters()

    # --- TEST 1: ZERO STIMULUS (BASELINE STABILITY) ---
    print("\n[Test 1] Zero-Stimulus Baseline Stability")
    _, y_zero, bold_zero, valid_zero = run_simulation(params, stim_freq=0.0)
    
    # Check if max deviation from initial conditions is effectively zero
    max_deviation_V = np.max(np.abs(y_zero[0] - 1.0))
    max_deviation_bold = np.max(np.abs(bold_zero))
    
    if max_deviation_V < 1e-5 and max_deviation_bold < 1e-5:
        print("  ✅ PASS: System remains stable at equilibrium.")
    else:
        print(f"  ❌ FAIL: System drifts! Max BOLD deviation: {max_deviation_bold}%")

    # --- TEST 2 & 3: SOLVER COMPARISON & POSITIVITY ---
    print("\n[Test 2 & 3] Solver Comparison & Positivity Check (20 Hz Stimulus)")
    
    # Run RK45
    t0 = time.time()
    t_rk, y_rk, bold_rk, valid_rk = run_simulation(params, stim_freq=20.0, method='RK45')
    time_rk = time.time() - t0
    
    # Run Radau
    t0 = time.time()
    _, y_radau, bold_radau, valid_radau = run_simulation(params, stim_freq=20.0, method='Radau')
    time_radau = time.time() - t0

    print(f"  ▸ RK45  Execution Time: {time_rk:.4f} seconds | Valid Positivity: {valid_rk}")
    print(f"  ▸ Radau Execution Time: {time_radau:.4f} seconds | Valid Positivity: {valid_radau}")

    # Calculate absolute difference between solvers
    max_diff_bold = np.max(np.abs(bold_rk - bold_radau))
    print(f"  ▸ Max BOLD difference between solvers: {max_diff_bold:.6e}%")

    if max_diff_bold < 1e-2:
        print("  ✅ PASS: RK45 and Radau converge to the same solution.")
    else:
        print("  ⚠️ WARNING: Solvers diverge. System may be highly stiff.")

    # --- PLOTTING FOR VISUAL INSPECTION ---
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    
    axes[0].plot(t_rk, y_rk[1], label="Glutamate (RK45)", color='crimson')
    axes[0].plot(t_rk, y_radau[1], label="Glutamate (Radau)", color='black', linestyle=':')
    axes[0].set_title("Solver Comparison: Cleft Glutamate")
    axes[0].legend()
    
    axes[1].plot(t_rk, bold_rk, label="BOLD (RK45)", color='royalblue')
    axes[1].plot(t_rk, bold_radau, label="BOLD (Radau)", color='black', linestyle=':')
    axes[1].set_title("Solver Comparison: fMRI BOLD")
    axes[1].set_xlabel("Time (s)")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(result_path('exp_0_verification.png'), dpi=200)
    print("\n✅ Verification plot saved to results/exp_0_verification.png")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_experiment()