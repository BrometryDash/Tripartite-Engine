"""
Experiment 2: TBOA Dose-Response Analysis
Simulates the pharmacological blockade of EAAT glutamate transporters 
by systematically reducing the V_max parameter.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

SIM_WINDOW_S = 240  # seconds; see comment in run_tboa_experiment
PLOT_WINDOW_S = 180
STIM_START_S = 3.0


def run_tboa_experiment():
    print("="*50)
    print(" 🧪 EXPERIMENT 2: TBOA DOSE-RESPONSE (V_max Blockade)")
    print("="*50)

    base_params = get_baseline_parameters()
    baseline_Vmax = base_params['V_max']
    
    # 1.0 = Healthy, 0.10 = Severe TBOA poisoning
    vmax_fractions = [1.0, 0.75, 0.50, 0.25, 0.10]
    
    results = {
        "EAAT_Capacity_Pct": [],
        "Glutamate_AUC_uMs": [],
        "Peak_Ca_uM": [],
        "Peak_BOLD_Pct": [],
        "BOLD_TTP_s": [], # Time to Peak BOLD (absolute time; unstable on a plateau -- see README)
        "BOLD_T50_rise_s": [], # Time from stimulus onset to half-maximal BOLD (robust onset measure)
        "BOLD_FWHM_s": [] # Full width at half maximum of the BOLD response (robust duration measure)
    }

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    for frac in vmax_fractions:
        test_params = base_params.copy()
        test_params['V_max'] = baseline_Vmax * frac
        
        print(f" ▸ Simulating {int(frac*100)}% EAAT Capacity (V_max = {test_params['V_max']} uM/s)...")
        
        # The window must be long enough for the glutamate pool to clear completely. At 10% uptake
        # capacity that takes ~150 s; with the default 25 s window the AUC (and time-to-peak) were
        # truncated. Verified: AUC is unchanged between 240 s and 400 s.
        t, y, bold, is_valid = run_simulation(test_params, stim_freq=20.0, t_span=(0, SIM_WINDOW_S), method='RK45')
        
        G, C = y[1], y[3]
        
        # Biomarkers
        glut_auc = np.trapezoid(G, x=t)
        peak_ca = np.max(C)
        peak_bold = np.max(bold)
        ttp_bold = t[np.argmax(bold)]
        above_half = np.where(bold >= 0.5 * peak_bold)[0]
        t50_rise = t[above_half[0]] - STIM_START_S
        fwhm = t[above_half[-1]] - t[above_half[0]]
        
        results["EAAT_Capacity_Pct"].append(int(frac * 100))
        results["Glutamate_AUC_uMs"].append(round(glut_auc, 2))
        results["Peak_Ca_uM"].append(round(peak_ca, 4))
        results["Peak_BOLD_Pct"].append(round(peak_bold, 4))
        results["BOLD_TTP_s"].append(round(ttp_bold, 2))
        results["BOLD_T50_rise_s"].append(round(t50_rise, 2))
        results["BOLD_FWHM_s"].append(round(fwhm, 1))

        # Plotting the traces
        alpha_val = 1.0 if frac == 1.0 else 0.4 + (1.0 - frac) * 0.6
        label_str = f"{int(frac*100)}% Capacity"
        
        ax1.plot(t, G, alpha=alpha_val, linewidth=2, label=label_str)
        ax2.plot(t, bold, alpha=alpha_val, linewidth=2, label=label_str)

    # Convert and save
    df = pd.DataFrame(results)
    df.to_csv(result_path('exp_2_tboa_response.csv'), index=False)
    
    # Format plots
    ax1.set_xlim(0, PLOT_WINDOW_S)
    ax1.set_title("Extracellular Glutamate Pool Under Reduced Uptake")
    ax1.set_ylabel("Glutamate (uM)")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    ax2.set_title("Macroscopic BOLD Response to TBOA")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("BOLD Signal (%)")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(result_path('exp_2_tboa_response.png'), dpi=200)
    
    print("\n✅ Data exported to results/exp_2_tboa_response.csv")
    print("✅ Plot saved to results/exp_2_tboa_response.png")
    print("="*50 + "\n")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_tboa_experiment()