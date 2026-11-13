"""
Experiment 1: Frequency-Response Analysis
Investigates the non-linear relationship between neuronal firing rates, 
synaptic vesicle depletion, and macroscopic BOLD responses.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from _common import result_path
from core.solver import get_baseline_parameters, run_simulation

def run_frequency_sweep():
    print("="*50)
    print(" 🧪 EXPERIMENT 1: FREQUENCY RESPONSE SWEEP")
    print("="*50)

    params = get_baseline_parameters()
    frequencies = [1, 2, 3, 5, 10, 20, 40, 60, 80]  # 1-3 Hz added so the sweep covers the range used in experiments
    
    # Data storage
    results = {
        "Frequency_Hz": [],
        "Min_Vesicles_Frac": [],
        "Glutamate_AUC_uMs": [],
        "Peak_Ca_uM": [],
        "Peak_BOLD_Pct": []
    }

    for freq in frequencies:
        print(f" ▸ Simulating {freq} Hz burst...")
        t, y, bold, is_valid = run_simulation(params, stim_freq=freq, method='RK45')
        
        # Extract states: V=y[0], G=y[1], I=y[2], C=y[3]
        V, G, C = y[0], y[1], y[3]
        
        # Calculate Biomarkers
        min_v = np.min(V)
        glut_auc = np.trapezoid(G, x=t) # Area under the curve for Glutamate
        peak_ca = np.max(C)
        peak_bold = np.max(bold)
        
        # Store in dict
        results["Frequency_Hz"].append(freq)
        results["Min_Vesicles_Frac"].append(round(min_v, 4))
        results["Glutamate_AUC_uMs"].append(round(glut_auc, 2))
        results["Peak_Ca_uM"].append(round(peak_ca, 4))
        results["Peak_BOLD_Pct"].append(round(peak_bold, 4))

    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(results)
    csv_path = result_path('exp_1_frequency_response.csv')
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Data exported to {csv_path}")

    # --- PLOTTING ---
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    # Axis 1: Peak BOLD (Macroscopic)
    ax1.set_xlabel('Presynaptic Firing Frequency (Hz)', fontweight='bold')
    ax1.set_ylabel('Peak BOLD Response (%)', color='royalblue', fontweight='bold')
    ax1.plot(df["Frequency_Hz"], df["Peak_BOLD_Pct"], marker='o', color='royalblue', linewidth=2, markersize=8)
    ax1.tick_params(axis='y', labelcolor='royalblue')
    
    # Axis 2: Vesicle Depletion (Microscopic)
    ax2 = ax1.twinx()  
    ax2.set_ylabel('Vesicle Availability Minimum (%)', color='purple', fontweight='bold')
    ax2.plot(df["Frequency_Hz"], df["Min_Vesicles_Frac"] * 100, marker='s', color='purple', linestyle='--', linewidth=2, markersize=8)
    ax2.tick_params(axis='y', labelcolor='purple')
    ax2.set_ylim(0, 100)

    plt.title("Model Prediction: Non-linear Neurovascular Coupling", fontsize=14, pad=15)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(result_path('exp_1_frequency_response.png'), dpi=200)
    print("✅ Plot saved to results/exp_1_frequency_response.png")
    print("="*50 + "\n")
    
    # Print the table beautifully to the terminal
    print(df.to_string(index=False))

if __name__ == "__main__":
    # If pandas is missing, install it: pip install pandas
    run_frequency_sweep()