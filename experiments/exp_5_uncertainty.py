"""
Experiment 5: Global Uncertainty Propagation
Quantifies how uncertainty in nominal parameters affects predicted BOLD responses,
using empirical percentiles to generate a 95% simulation interval.
"""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_uncertainty_propagation(n_simulations=100):
    print("="*50)
    print(f" 🧪 EXPERIMENT 5: UNCERTAINTY PROPAGATION (N={n_simulations})")
    print("="*50)
    
    base_params = get_baseline_parameters()
    
    # Assumed Coefficient of Variation (CV) for Uncertainty Propagation
    # 5% for literature-derived, 20% for phenomenological/coupling
    uncertainty_map = {
        'tau_rec': 0.05, 'U': 0.05, 'K_m': 0.05, 'kappa': 0.05, 
        'gamma': 0.05, 'tau_0': 0.05, 'alpha': 0.05, 'E_0': 0.05, 
        'V_max': 0.20, 'rho': 0.20, 'K_G': 0.20, 'k_prod': 0.20, 
        'k_deg': 0.20, 'J_max': 0.20, 'K_I': 0.20, 'tau_Ca': 0.20, 'epsilon': 0.20 
    }
    
    # Use a reproducible random seed
    rng = np.random.default_rng(42)
    
    all_bolds = []
    time_array = None

    for i in range(n_simulations):
        noisy_params = {}
        for param, base_val in base_params.items():
            cv = uncertainty_map[param]
            # Generate noisy parameter, bounded to strictly positive values
            noisy_val = max(1e-4, rng.normal(loc=base_val, scale=base_val * cv))
            noisy_params[param] = noisy_val
            
        t, _, bold, is_valid = run_simulation(noisy_params, stim_freq=20.0, method='RK45')
        
        if time_array is None: 
            time_array = t
        
        # Only keep simulations that didn't mathematically crash
        if is_valid:
            all_bolds.append(bold)
        
        if (i+1) % 20 == 0:
            print(f" ▸ Completed {i+1}/{n_simulations} simulations")

    all_bolds = np.array(all_bolds)
    # time to peak of every individual run, relative to stimulus onset (3 s), for comparison with
    # measured subject-to-subject variability
    run_ttps = time_array[np.argmax(all_bolds, axis=1)] - 3.0
    
    # Calculate empirical percentiles (No Gaussian assumption on the output)
    median_bold = np.percentile(all_bolds, 50, axis=0)
    ci_lower = np.percentile(all_bolds, 2.5, axis=0)  # Lower 95% bound
    ci_upper = np.percentile(all_bolds, 97.5, axis=0) # Upper 95% bound

    # --- SAVE DATA ---
    df_out = pd.DataFrame({
        "Time_s": time_array,
        "Median_BOLD": median_bold,
        "Lower_95_CI": ci_lower,
        "Upper_95_CI": ci_upper
    })
    df_out.to_csv(result_path('exp_5_uncertainty.csv'), index=False)
    
    summary = {
        "N_simulations_attempted": n_simulations,
        "N_simulations_valid": len(all_bolds),
        "Median_Peak_BOLD_Pct": round(float(np.max(median_bold)), 2),
        "Upper_Bound_Peak_Pct": round(float(np.max(ci_upper)), 2),
        "Lower_Bound_Peak_Pct": round(float(np.max(ci_lower)), 2),
        # spread of the individual runs' BOLD time to peak (s after stimulus onset)
        "BOLD_TTP_min_s": round(float(np.min(run_ttps)), 2),
        "BOLD_TTP_median_s": round(float(np.median(run_ttps)), 2),
        "BOLD_TTP_max_s": round(float(np.max(run_ttps)), 2)
    }
    with open(result_path('exp_5_uncertainty_summary.json'), 'w') as f:
        json.dump(summary, f, indent=4)

    # --- PLOTTING ---
    plt.figure(figsize=(9, 6))
    
    # Plot spaghetti traces in background
    for i in range(min(40, len(all_bolds))):
        plt.plot(time_array, all_bolds[i], color='gray', alpha=0.1)
        
    plt.plot(time_array, median_bold, color='royalblue', linewidth=2.5, label='Median Predicted BOLD')
    plt.fill_between(time_array, ci_lower, ci_upper, color='royalblue', alpha=0.3, label='95% Simulation Interval')
    
    plt.title(f"Parameter-Induced Uncertainty Band (N={len(all_bolds)} Valid Runs)", fontsize=14, pad=15)
    plt.xlabel('Time (s)', fontweight='bold')
    plt.ylabel('fMRI BOLD Signal (%)', fontweight='bold')
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(result_path('exp_5_uncertainty.png'), dpi=200)
    
    print("\n✅ Time-series data exported to results/exp_5_uncertainty.csv")
    print("✅ JSON Summary exported to results/exp_5_uncertainty_summary.json")
    print("✅ Plot saved to results/exp_5_uncertainty.png")
    print("="*50 + "\n")
    print(f"Summary: Peak BOLD Median = {summary['Median_Peak_BOLD_Pct']}% (95% Interval: {summary['Lower_Bound_Peak_Pct']}% to {summary['Upper_Bound_Peak_Pct']}%)")

if __name__ == "__main__":
    run_uncertainty_propagation()