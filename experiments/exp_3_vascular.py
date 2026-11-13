"""
Experiment 3: Vascular Impairment (Neurovascular Uncoupling)
Simulates aging or ischemic conditions where neural and astrocytic signaling 
are perfectly normal, but vascular compliance and oxygen extraction are impaired.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_vascular_experiment():
    print("="*50)
    print(" 🧪 EXPERIMENT 3: VASCULAR IMPAIRMENT (Ischemia/Aging)")
    print("="*50)

    base_params = get_baseline_parameters()
    
    conditions = [
        {"name": "Healthy", "alpha": 0.33, "E_0": 0.40},
        {"name": "Mild Stiffness", "alpha": 0.25, "E_0": 0.45},
        {"name": "Severe Stiffness", "alpha": 0.15, "E_0": 0.55}
    ]
    
    results = {
        "Condition": [],
        "Peak_Ca_uM": [],
        "Peak_Flow_Pct": [],
        "Peak_BOLD_Pct": [],
        "BOLD_TTP_s": []
    }

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)
    colors = ['royalblue', 'darkorange', 'crimson']

    for i, cond in enumerate(conditions):
        test_params = base_params.copy()
        test_params['alpha'] = cond['alpha']
        test_params['E_0'] = cond['E_0']
        
        print(f" ▸ Simulating {cond['name']} (alpha={cond['alpha']}, E_0={cond['E_0']})...")
        
        t, y, bold, is_valid = run_simulation(test_params, stim_freq=20.0, method='RK45')
        
        C, f = y[3], y[5]
        
        # Biomarkers
        peak_ca = np.max(C)
        peak_flow = np.max(f - 1.0) * 100 # Convert to % change
        peak_bold = np.max(bold)
        ttp_bold = t[np.argmax(bold)]
        
        results["Condition"].append(cond['name'])
        results["Peak_Ca_uM"].append(round(peak_ca, 4))
        results["Peak_Flow_Pct"].append(round(peak_flow, 2))
        results["Peak_BOLD_Pct"].append(round(peak_bold, 2))
        results["BOLD_TTP_s"].append(round(ttp_bold, 2))

        # Plotting
        ax1.plot(t, C, color=colors[i], linewidth=3, alpha=0.7, linestyle='--' if i>0 else '-', label=f"Ca2+ ({cond['name']})")
        ax2.plot(t, bold, color=colors[i], linewidth=2.5, label=f"BOLD ({cond['name']})")

    # Convert and save
    df = pd.DataFrame(results)
    df.to_csv(result_path('exp_3_vascular_impairment.csv'), index=False)
    
    # Format plots
    ax1.set_title("Upstream Signal: Astrocyte Calcium")
    ax1.set_ylabel("Cytosolic Ca2+ (uM)")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Downstream Signal: Macroscopic BOLD")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("BOLD Signal (%)")
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(result_path('exp_3_vascular_impairment.png'), dpi=200)
    
    print("\n✅ Data exported to results/exp_3_vascular_impairment.csv")
    print("✅ Plot saved to results/exp_3_vascular_impairment.png")
    print("="*50 + "\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_vascular_experiment()