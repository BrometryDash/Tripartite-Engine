"""
Diagnostic Run: Causal Chain Tracing
Runs the 20Hz baseline simulation for 100 seconds to trace signal amplification 
and temporal delays through all 8 state variables.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_diagnostic():
    print("="*60)
    print(" 🩺 DIAGNOSTIC RUN: TRACING THE CAUSAL CHAIN")
    print("="*60)

    params = get_baseline_parameters()
    
    # 20 Hz stimulus, extending simulation to 100 seconds
    t, y, bold, is_valid = run_simulation(
        params, stim_freq=20.0, stim_start=3.0, stim_end=5.0, t_span=(0, 100), method='RK45'
    )
    
    V, G, I, C, s, f, v, q = y
    
    # We want to find the max deviation from baseline. 
    # For variables that drop (like V and q), we find the minimum.
    metrics = []
    
    state_vars = [
        ("Vesicles (V)", V, "min"),
        ("Glutamate (G)", G, "max"),
        ("IP3 (I)", I, "max"),
        ("Calcium (C)", C, "max"),
        ("Vaso Signal (s)", s, "max"),
        ("Blood Flow (f)", f, "max"),
        ("Blood Vol (v)", v, "max"),
        ("DeoxyHb (q)", q, "min"),
        ("BOLD (%)", bold, "max")
    ]
    
    stim_start = 3.0

    for name, trace, extremum in state_vars:
        baseline = trace[0]
        
        if extremum == "max":
            peak_val = np.max(trace)
            ttp_idx = np.argmax(trace)
        else:
            peak_val = np.min(trace)
            ttp_idx = np.argmin(trace)
            
        ttp_relative = t[ttp_idx] - stim_start  # time to peak relative to stimulus onset
            
        metrics.append({
            "Variable": name,
            "Baseline": round(baseline, 4),
            "Peak_Value": round(peak_val, 4),
            "Max_Deviation": round(abs(peak_val - baseline), 4),
            "Time_to_Peak_s": round(ttp_relative, 2)
        })

    df = pd.DataFrame(metrics)
    df.to_csv(result_path('diagnostic_chain.csv'), index=False)
    
    # --- PLOTTING THE CAUSAL CHAIN ---
    fig, axes = plt.subplots(4, 2, figsize=(12, 10), sharex=True)
    axes = axes.flatten()
    
    traces = [G, I, C, s, f, v, q, bold]
    titles = ["1. Glutamate (G)", "2. IP3 (I)", "3. Calcium (C)", "4. Vaso Signal (s)", 
              "5. Blood Flow (f)", "6. Blood Vol (v)", "7. DeoxyHb (q)", "8. BOLD Signal"]
    colors = ['crimson', 'gray', 'darkorange', 'purple', 'teal', 'indianred', 'black', 'royalblue']
    
    for i in range(8):
        axes[i].plot(t, traces[i], color=colors[i], linewidth=2)
        axes[i].set_title(titles[i], fontweight='bold')
        axes[i].axvspan(3.0, 5.0, color='gray', alpha=0.2) # Stimulus window
        axes[i].grid(True, alpha=0.3)
        if i >= 6:
            axes[i].set_xlabel("Time (s)")

    plt.tight_layout()
    plt.savefig(result_path('diagnostic_chain.png'), dpi=200)
    
    print(df.to_string(index=False))
    print("\n✅ Diagnostic plot saved to results/diagnostic_chain.png")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_diagnostic()