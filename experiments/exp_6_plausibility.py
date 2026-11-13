"""
Experiment 6: Model Plausibility and Literature Comparison
Compares the normalized temporal dynamics (Time-to-Peak, undershoot) of the 
simulated BOLD response against a canonical Double-Gamma HRF used in neuroimaging.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import gamma

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def canonical_hrf(t):
    """
    Standard SPM Double-Gamma HRF.
    Peak at ~5s, undershoot at ~15s.
    """
    # SPM default parameters
    peak_delay = 6.0
    under_delay = 16.0
    peak_disp = 1.0
    under_disp = 1.0
    ratio = 1.0 / 6.0
    
    hrf = gamma.pdf(t, peak_delay/peak_disp, scale=peak_disp) - ratio * gamma.pdf(t, under_delay/under_disp, scale=under_disp)
    return hrf / np.max(hrf) # Normalize to peak of 1.0

def run_plausibility_check():
    print("="*50)
    print(" 🧪 EXPERIMENT 6: PLAUSIBILITY & LITERATURE COMPARISON")
    print("="*50)

    params = get_baseline_parameters()
    
    # 1-second brief stimulus (like a standard fMRI event-related task)
    stim_start = 3.0
    stim_end = 4.0
    
    t, _, bold, _ = run_simulation(params, stim_freq=20.0, stim_start=stim_start, stim_end=stim_end, t_span=(0, 30), method='RK45')
    
    # Normalize simulated BOLD
    sim_bold_norm = bold / np.max(bold)
    
    # Generate canonical HRF shifted to stimulus start
    t_hrf = np.maximum(0, t - stim_start)
    canonical_bold = canonical_hrf(t_hrf)
    
    # Calculate Biomarkers for comparison
    sim_ttp = t[np.argmax(sim_bold_norm)] - stim_start
    can_ttp = t[np.argmax(canonical_bold)] - stim_start
    
    print(f" ▸ Simulated Time-to-Peak (TTP): {sim_ttp:.2f} seconds")
    print(f" ▸ Canonical Time-to-Peak (TTP): {can_ttp:.2f} seconds")
    
    # --- SAVE DATA ---
    df = pd.DataFrame({
        "Time_s": t,
        "Simulated_BOLD_Norm": sim_bold_norm,
        "Canonical_HRF_Norm": canonical_bold
    })
    df.to_csv(result_path('exp_6_plausibility.csv'), index=False)

    # --- PLOTTING ---
    plt.figure(figsize=(8, 5))
    
    # Stimulus window shaded
    plt.axvspan(stim_start, stim_end, color='gray', alpha=0.2, label='1s Neural Stimulus')
    
    plt.plot(t, sim_bold_norm, color='royalblue', linewidth=3, label=f'Simulated ODE Model (TTP: {sim_ttp:.1f}s)')
    plt.plot(t, canonical_bold, color='black', linestyle='--', linewidth=2, label=f'Empirical SPM HRF (TTP: {can_ttp:.1f}s)')
    
    plt.title("Model Plausibility: Temporal HRF Dynamics", fontsize=14, pad=15)
    plt.xlabel('Time (s)', fontweight='bold')
    plt.ylabel('Normalized BOLD Response', fontweight='bold')
    plt.legend(loc="upper right")
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(result_path('exp_6_plausibility.png'), dpi=200)
    
    print("\n✅ Data exported to results/exp_6_plausibility.csv")
    print("✅ Plot saved to results/exp_6_plausibility.png")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_plausibility_check()