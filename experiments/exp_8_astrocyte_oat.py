"""
Experiment 8: Controlled Astrocytic Temporal Sensitivity
Performs a One-At-a-Time (OAT) temporal acceleration on astrocytic parameters
to identify which specific mechanism governs the Ca2+ latency.

The two upstream (glutamate pool) parameters V_max (uptake, x4) and rho (release, /4) are included as
controls. Without them the experiment cannot tell whether the delay comes from the astrocyte or from the
time the glutamate pool takes to clear.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_astrocyte_temporal_oat():
    print("="*60)
    print(" ⏱️ EXPERIMENT 8: CONTROLLED ASTROCYTIC TEMPORAL OAT")
    print("="*60)

    base_params = get_baseline_parameters()
    stim_start = 3.0
    
    # Baseline Ca2+ TTP
    t_base, y_base, _, _ = run_simulation(base_params, stim_freq=20.0, method='RK45')
    base_ca_ttp = t_base[np.argmax(y_base[3])] - stim_start
    print(f" ▸ Baseline Ca2+ TTP: {base_ca_ttp:.2f} s")

    # Parameters to accelerate (Rate * 4, or Time Constant / 4)
    temporal_params = ['k_prod', 'k_deg', 'J_max', 'tau_Ca', 'V_max', 'rho']
    upstream_params = {'V_max', 'rho'}   # glutamate pool, not astrocyte
    acceleration_factor = 4.0
    
    results = {"Parameter": [], "Module": [], "New_Ca2_TTP_s": [], "TTP_Reduction_s": []}

    for param in temporal_params:
        test_params = base_params.copy()
        if param in ('tau_Ca', 'rho'):   # time constant, or release scale (less release = faster clearance)
            test_params[param] /= acceleration_factor
        else:
            test_params[param] *= acceleration_factor
            
        t, y, _, _ = run_simulation(test_params, stim_freq=20.0, method='RK45')
        ca_ttp = t[np.argmax(y[3])] - stim_start
        reduction = base_ca_ttp - ca_ttp
        
        results["Parameter"].append(param)
        results["Module"].append("glutamate pool" if param in upstream_params else "astrocyte")
        results["New_Ca2_TTP_s"].append(round(ca_ttp, 2))
        results["TTP_Reduction_s"].append(round(reduction, 2))
        print(f" ▸ Accelerated {param:7s} -> New TTP: {ca_ttp:.2f} s (Reduced by {reduction:.2f} s)")

    df = pd.DataFrame(results)
    df.to_csv(result_path('exp_8_astrocyte_oat.csv'), index=False)

    # Plotting
    df = df.sort_values(by="TTP_Reduction_s", ascending=True)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['steelblue' if m == 'glutamate pool' else 'darkorange' for m in df["Module"]]
    ax.barh(df["Parameter"], df["TTP_Reduction_s"], color=colors)
    ax.set_xlabel('Reduction in Ca2+ Time-to-Peak (seconds)')
    ax.set_title('Temporal Bottleneck Isolation (4x change; orange = astrocyte, blue = glutamate pool)')
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(result_path('exp_8_astrocyte_oat.png'), dpi=200)
    print("\n✅ Plot saved to results/exp_8_astrocyte_oat.png")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_astrocyte_temporal_oat()
    