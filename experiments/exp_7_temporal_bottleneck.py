"""
Experiment 7: Temporal Bottleneck Analysis
Systematically accelerates the phenomenological astrocytic module to determine
if the BOLD Time-to-Peak (TTP) delay (~12.2 s for the 2 s baseline pulse used here; ~10.6 s for
the 1 s pulse of Experiment 6) originates primarily from astrocytic IP3/Ca2+ signaling or from
downstream hemodynamics.

Note: only the astrocytic rates are accelerated here. Upstream parameters (glutamate release rho
and uptake V_max) are NOT varied, so this experiment cannot attribute the delay to the astrocyte
versus the time the glutamate pool takes to clear -- see README, 'Known limitations'.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_temporal_bottleneck_analysis():
    print("="*60)
    print(" ⏱️ EXPERIMENT 7: TEMPORAL BOTTLENECK ANALYSIS")
    print("="*60)

    base_params = get_baseline_parameters()
    
    # We will scale the astrocytic rates by a multiplier (1x = Baseline, 10x = Extremely fast)
    speed_multipliers = [1.0, 2.0, 4.0, 8.0, 16.0]
    
    results = {
        "Astrocyte_Speed_Factor": [],
        "Ca2_TTP_s": [],
        "Flow_TTP_s": [],
        "BOLD_TTP_s": []
    }

    # Plotting setup
    fig, axes = plt.subplots(3, 1, figsize=(8, 10), sharex=True)
    colors = plt.cm.viridis(np.linspace(0, 0.9, len(speed_multipliers)))

    for idx, speed in enumerate(speed_multipliers):
        test_params = base_params.copy()
        
        # Accelerate the astrocytic module
        test_params['k_prod'] = base_params['k_prod'] * speed
        test_params['k_deg'] = base_params['k_deg'] * speed
        test_params['J_max'] = base_params['J_max'] * speed
        test_params['tau_Ca'] = base_params['tau_Ca'] / speed
        
        # To maintain the same amplitude of Ca2+ for a fair temporal comparison,
        # we don't change affinities (K_G, K_I), only rates.
        
        print(f" ▸ Simulating Astrocytic Speed: {speed}x...")
        t, y, bold, is_valid = run_simulation(
            test_params, stim_freq=20.0, stim_start=3.0, stim_end=5.0, t_span=(0, 30), method='RK45'
        )
        
        C, f = y[3], y[5]
        
        # Calculate Time-to-Peak (Relative to stimulus start at 3.0s)
        stim_start = 3.0
        ca_ttp = t[np.argmax(C)] - stim_start
        flow_ttp = t[np.argmax(f)] - stim_start
        bold_ttp = t[np.argmax(bold)] - stim_start
        
        results["Astrocyte_Speed_Factor"].append(f"{speed}x")
        results["Ca2_TTP_s"].append(round(ca_ttp, 2))
        results["Flow_TTP_s"].append(round(flow_ttp, 2))
        results["BOLD_TTP_s"].append(round(bold_ttp, 2))

        # Traces
        axes[0].plot(t, C, color=colors[idx], linewidth=2, label=f"{speed}x Speed")
        axes[1].plot(t, f - 1.0, color=colors[idx], linewidth=2)
        axes[2].plot(t, bold, color=colors[idx], linewidth=2)

    # --- FORMATTING PLOTS ---
    axes[0].set_title("Astrocytic Calcium (C)")
    axes[0].set_ylabel("Ca2+ (uM)")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)
    axes[0].axvspan(3.0, 5.0, color='gray', alpha=0.2)

    axes[1].set_title("Macroscopic Blood Flow (f)")
    axes[1].set_ylabel("Flow Change")
    axes[1].grid(True, alpha=0.3)
    axes[1].axvspan(3.0, 5.0, color='gray', alpha=0.2)

    axes[2].set_title("Macroscopic BOLD Signal")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_ylabel("BOLD (%)")
    axes[2].grid(True, alpha=0.3)
    axes[2].axvspan(3.0, 5.0, color='gray', alpha=0.2)

    plt.tight_layout()
    plt.savefig(result_path('exp_7_temporal_bottleneck.png'), dpi=200)
    
    df = pd.DataFrame(results)
    df.to_csv(result_path('exp_7_temporal_bottleneck.csv'), index=False)
    
    print("\n✅ Data exported to results/exp_7_temporal_bottleneck.csv")
    print("✅ Plot saved to results/exp_7_temporal_bottleneck.png")
    print("="*60 + "\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_temporal_bottleneck_analysis()