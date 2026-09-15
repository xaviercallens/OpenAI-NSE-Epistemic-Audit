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
L_ref = 0.01   # Reference vortex core radius (m), matching the value used
               # consistently elsewhere in this project (e.g.
               # scripts/directive5_mach_divergence.py, physics_constants.py)


def generate_falsification_graphs(out_path=None):
    """Generates dual-panel falsification plot."""
    tau = np.logspace(-2, -15, 500)
    # Panel 1 plots the LOCAL enstrophy density |omega|^2 ~ tau^(-2-2h) of the
    # core (dimensionless tau; prefactor (u0/L_ref)^2 with u0 = nu/L_ref), not
    # the integrated enstrophy ~ tau^(-0.515) as an earlier version labelled it.
    # The physical ceiling is the local vorticity bound |omega|_max = c_s^2/nu
    # (Ma < 1 and Kn < 1 together), squared; the previous constant 1.13e13 had
    # no derivation.
    omega_math = (nu / L_ref) ** 2 * (tau ** -2.01)
    omega_phys_max = (c_s ** 2 / nu) ** 2
    omega_physics = np.minimum(omega_math, omega_phys_max)

    # u0 = nu / L_ref (reference viscous velocity), consistent with
    # directive5_mach_divergence.py and workflowresearch1.py; a previous
    # version hardcoded 1.18e-4 here, ~18% higher than nu/L_ref and with no
    # stated derivation, while every other script in this project uses
    # nu/L_ref ~ 1.0e-4.
    u0 = nu / L_ref
    velocity_math = u0 * (tau ** -0.505)
    mach_number = velocity_math / c_s

    mach_breach_idx = np.where(mach_number > 0.3)[0][0]
    tau_mach_breach = tau[mach_breach_idx]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

    # Subplot 1: Enstrophy Divergence vs Physical Reality
    ax1.loglog(tau, omega_math, 'r--', label=r'OpenAI core: local $|\omega|^2 \sim \tau^{-2.01}$')
    ax1.loglog(tau, omega_physics, 'b-', linewidth=3, label='Capped at model-validity bound')
    ax1.axhline(omega_phys_max, color='k', linestyle=':', label=r'$(c_s^2/\nu)^2$: Ma$<$1 and Kn$<$1 (water)')
    ax1.axvline(tau_mach_breach, color='orange', linestyle='-', linewidth=2, label=rf'Mach 0.3 at $\tau \approx {tau_mach_breach:.1e}$ ($t = 100\,\tau$ s)')

    ax1.set_xlim(1e-2, 1e-15)
    ax1.set_ylim(1e-4, 1e28)
    ax1.set_xlabel(r'Dimensionless time to singularity $\tau$ (physical $t = 100\,\tau$ s for $\ell_0 = 1$ cm)')
    ax1.set_ylabel(r'Local enstrophy density $|\omega|^2$ (s$^{-2}$)')
    ax1.set_title('Core vorticity vs. continuum-model validity bound (water)')
    ax1.grid(True, which="both", ls="-", alpha=0.2)
    ax1.legend(loc='upper right')

    # Subplot 2: Mach Number Invalidation
    ax2.loglog(tau, mach_number, 'g-', linewidth=2, label='Local Mach Number ($Ma$)')
    ax2.axhline(0.3, color='r', linestyle='--', label='Incompressibility Threshold ($Ma = 0.3$)')
    ax2.axvline(tau_mach_breach, color='orange', linestyle='-', linewidth=2)
    ax2.fill_between(tau[mach_breach_idx:], 0.3, mach_number[mach_breach_idx:], color='red', alpha=0.2, label='Unphysical (Compressible/Shock Regime)')

    ax2.set_xlim(1e-2, 1e-15)
    ax2.set_ylim(1e-6, 1e3)
    ax2.set_xlabel(r'Dimensionless time to singularity $\tau$ (physical $t = 100\,\tau$ s for $\ell_0 = 1$ cm)')
    ax2.set_ylabel('Mach Number $Ma$')
    ax2.set_title('Incompressibility breakdown of the core')
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
