import json
import numpy as np
import matplotlib.pyplot as plt
import os

# Path to LeanFlow JHTDB data
leanflow_data_path = "/home/xavkal/xdev/SocrateAI-Numeric-DualScale-Solver/SocrateAI-Numeric-DualScale-Solver/data/output/jhtdb_openfoam_real_comparison.json"

with open(leanflow_data_path, "r") as f:
    data = json.load(f)

k_vals = np.array(data["jhtdb_spectrum"]["k_vals"])[1:] # Skip k=0
E_k_real = np.array(data["jhtdb_spectrum"]["E_k"])[1:]

# OpenAI Pathological Spectrum (Theoretical Model)
# Energy concentrates at shrinking scale lambda(tau) ~ tau^(0.5)
# Therefore peak wavenumber k_peak ~ tau^(-0.5) -> infinity.
# Let's model a snapshot at tau = 1e-6 where k_peak is shifted very high
# with a narrow Gevrey-2 wave packet spectrum.
k_openai = np.logspace(0, 3, 100)
E_k_openai = 1000 * np.exp(- (np.log10(k_openai) - 2.5)**2 / 0.1)  # Gevrey-like spike at high k

plt.figure(figsize=(9, 6))

# Plot JHTDB Real Data
plt.loglog(k_vals, E_k_real, 'bo-', label='Real Turbulence (JHTDB Isotropic)', linewidth=2, markersize=8)

# Plot Kolmogorov -5/3 Reference
kolmogorov_ref = E_k_real[1] * (k_vals / k_vals[1])**(-5./3.)
plt.loglog(k_vals, kolmogorov_ref, 'k--', label='Kolmogorov $k^{-5/3}$ scaling', linewidth=2)

# Plot OpenAI Snapshot
plt.loglog(k_openai, E_k_openai, 'r-', label='OpenAI Pre-Singularity Snapshot ($\\tau = 10^{-6}$)', linewidth=2)

plt.xlabel('Wavenumber $k$', fontsize=14)
plt.ylabel('Energy Spectrum $E(k)$', fontsize=14)
plt.title('Energy Spectrum: Physical Turbulence vs Manufactured Singularity', fontsize=15)
plt.legend(fontsize=12)
plt.grid(True, which="both", ls="--", alpha=0.5)

# Save plot to figures folder
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../01_Verification_Paper/spectrum_comparison.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"Saved plot to {out_path}")
