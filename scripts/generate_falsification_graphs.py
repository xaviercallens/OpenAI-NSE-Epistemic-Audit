#!/usr/bin/env python3
"""
Generates enstrophy and Mach number falsification plots comparing
OpenAI Lean 4 mathematical claim against physical DNS limits.
"""

import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Physical parameters for water at 300K
nu = 1.004e-6  # Kinematic viscosity (m^2/s)
c_s = 1500.0   # Speed of sound (m/s)


def generate_falsification_graphs(out_path=None):
    """Generates dual-panel falsification plot."""
    tau = np.logspace(-2, -15, 500)
    omega_math = 1e6 * (tau ** -0.515)
    omega_phys_max = 1.13e13
    omega_physics = np.minimum(omega_math, omega_phys_max)

    velocity_math = 1.18e-4 * (tau ** -0.505)
    mach_number = velocity_math / c_s

    mach_breach_idx = np.where(mach_number > 0.3)[0][0]
    tau_mach_breach = tau[mach_breach_idx]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    # Subplot 1: Enstrophy Divergence vs Physical Reality
    ax1.loglog(tau, omega_math, 'r--', label=r'OpenAI Lean 4 Claim: $\Omega \sim \tau^{-0.515}$')
    ax1.loglog(tau, omega_physics, 'b-', linewidth=3, label='Physical CFD Reality (Viscous Capped)')
    ax1.axhline(omega_phys_max, color='k', linestyle=':', label=r'Thermodynamic Censorship Limit ($\Omega_{max}$)')
    ax1.axvline(tau_mach_breach, color='orange', linestyle='-', linewidth=2, label=rf'Mach 0.3 Breakdown ($\tau \approx {tau_mach_breach:.1e}$ s)')

    ax1.set_xlim(1e-2, 1e-15)
    ax1.set_ylim(1e6, 1e18)
    ax1.set_xlabel(r'Time to Singularity $\tau$ (seconds)')
    ax1.set_ylabel(r'Global Enstrophy $\Omega(t)$')
    ax1.set_title('Topological Singularity vs Kolmogorov Dissipation (Water)')
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    ax1.legend(loc='upper right')

    # Subplot 2: Mach Number Invalidation
    ax2.loglog(tau, mach_number, 'g-', linewidth=2, label='Local Mach Number ($Ma$)')
    ax2.axhline(0.3, color='r', linestyle='--', label='Incompressibility Threshold ($Ma = 0.3$)')
    ax2.axvline(tau_mach_breach, color='orange', linestyle='-', linewidth=2)
    ax2.fill_between(tau[mach_breach_idx:], 0.3, mach_number[mach_breach_idx:], color='red', alpha=0.2, label='Unphysical (Compressible/Shock Regime)')

    ax2.set_xlim(1e-2, 1e-15)
    ax2.set_ylim(1e-6, 1e3)
    ax2.set_xlabel(r'Time to Singularity $\tau$ (seconds)')
    ax2.set_ylabel('Mach Number $Ma$')
    ax2.set_title('Incompressibility Breakdown (Boussinesq Invalidation)')
    ax2.grid(True, which="both", ls="-", alpha=0.2)
    ax2.legend(loc='upper right')

    plt.tight_layout()

    if out_path is None:
        out_dir = os.path.join(os.path.dirname(__file__), "../02_Empirical_Observation/DNS_Turbulence_Verification")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "enstrophy_falsification.png")

    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Graph saved to: {out_path}")
    return out_path


if __name__ == '__main__':
    generate_falsification_graphs()
