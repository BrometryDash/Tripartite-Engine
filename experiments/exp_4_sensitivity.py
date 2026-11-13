"""
Experiment 4: Local Normalized Sensitivity Analysis
Calculates the dimensionless sensitivity coefficient (S_i) for each parameter 
to determine which assumptions most strongly govern the Peak BOLD response.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_sensitivity():
    print("="*50)
    print(" 🧪 EXPERIMENT 4: LOCAL SENSITIVITY ANALYSIS (OAT)")
    print("="*50)
    
    base_params = get_baseline_parameters()
    
    # Baseline run
    _, _, base_bold, _ = run_simulation(base_params, method='RK45')
    base_peak = np.max(base_bold)
    print(f" ▸ Baseline Peak BOLD: {base_peak:.4f}%")
    
    results = {
        "Parameter": [],
        "S_i_Coefficient": []
    }
    
    perturbation_fraction = 0.10  # +10% increase
    
    for param_name, base_val in base_params.items():
        test_params = base_params.copy()
        test_params[param_name] = base_val * (1.0 + perturbation_fraction)
        
        _, _, test_bold, _ = run_simulation(test_params, method='RK45')
        test_peak = np.max(test_bold)
        
        # Dimensionless Sensitivity Coefficient (S_i = (dY/Y) / (dP/P))
        delta_y_frac = (test_peak - base_peak) / base_peak
        s_i = delta_y_frac / perturbation_fraction
        
        results["Parameter"].append(param_name)
        results["S_i_Coefficient"].append(round(s_i, 4))
        print(f" ▸ {param_name:10s} : S_i = {s_i:+.4f}")

    df = pd.DataFrame(results)
    
    # Sort by absolute magnitude of sensitivity for the plot
    df['Abs_S_i'] = df['S_i_Coefficient'].abs()
    df = df.sort_values(by='Abs_S_i', ascending=True).drop(columns=['Abs_S_i'])
    
    # --- PLOTTING TORNADO CHART ---
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = ['crimson' if val < 0 else 'royalblue' for val in df['S_i_Coefficient']]
    ax.barh(df['Parameter'], df['S_i_Coefficient'], color=colors)
    
    ax.set_xlabel('Dimensionless Sensitivity Coefficient ($S_i$)', fontsize=12, fontweight='bold')
    ax.set_title('Local Sensitivity of Peak BOLD to +10% Parameter Perturbations', fontsize=14, pad=15)
    
    # Add vertical line at 0
    ax.axvline(0, color='black', linewidth=1)
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    df.to_csv(result_path('exp_4_sensitivity.csv'), index=False)
    plt.savefig(result_path('exp_4_sensitivity.png'), dpi=200)
    
    print("\n✅ Data exported to results/exp_4_sensitivity.csv")
    print("✅ Plot saved to results/exp_4_sensitivity.png")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_sensitivity()