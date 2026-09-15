#!/usr/bin/env python3
"""
Directive 5: Mach Number Divergence — Physical Self-Invalidation

Tracks the local Mach number Ma = |u|/c_s of the OpenAI collapsing vortex
core as tau -> 0, demonstrating that the incompressibility assumption
(Ma << 1) breaks down BEFORE the mathematical blowup time.
"""

import numpy as np
import os
import sys

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from physics_constants import (
    WATER_300K, BOLTZMANN_CONSTANT, ANISOTROPY_H_DEFAULT,
    MACH_INCOMPRESSIBILITY_LIMIT, SONIC_MACH_LIMIT,
    L_REF_DEFAULT, get_reference_velocity
)

# Physical Constants (Water at 300K) from Unified Repository
c_s = WATER_300K.speed_of_sound           # Speed of sound in water (m/s)
nu = WATER_300K.kinematic_viscosity       # Kinematic viscosity of water (m²/s)
rho = WATER_300K.density                  # Density (kg/m³)
k_B = BOLTZMANN_CONSTANT                  # Boltzmann constant (J/K)
T = 300.0                                 # Temperature (K)
c_p_water = WATER_300K.isobaric_heat_capacity  # Specific heat capacity (J/(kg·K))
mfp_water = WATER_300K.mean_free_path     # Intermolecular mean free path (m)

# Anisotropy parameter (from the paper: h < 1/100)
h = ANISOTROPY_H_DEFAULT                  # h = 1/200 = 0.005

# Reference Scales
L_ref = L_REF_DEFAULT                     # Macroscopic reference length (0.01 m = 1 cm)
u_ref = get_reference_velocity(WATER_300K, L_ref)  # ~ 10^{-4} m/s (viscous velocity scale)


def velocity(tau, u_0=u_ref, h_param=h):
    """Peak velocity at the vortex core edge."""
    return u_0 * tau ** (-0.5 - h_param)


def mach_number(tau, u_0=u_ref, c_sound=c_s, h_param=h):
    """Local Mach number."""
    return velocity(tau, u_0, h_param) / c_sound


def core_radius(tau, l_0=L_ref):
    """Radial scale of the vortex core."""
    return l_0 * tau ** 0.5


def reynolds_angular(tau, u_0=u_ref, l_0=L_ref, nu_val=nu, h_param=h):
    """Angular Reynolds number ~ u_theta * l_r / nu."""
    return velocity(tau, u_0, h_param) * core_radius(tau, l_0) / nu_val


def temperature_rise(tau, u_0=u_ref, l_0=L_ref, nu_val=nu, c_p=c_p_water, h_param=h):
    """
    Local temperature rise from viscous dissipation.
    Delta_T ~ nu * |curl u|^2 * tau / (rho * c_p)
    |curl u| ~ u_theta / l_r
    """
    vorticity = velocity(tau, u_0, h_param) / core_radius(tau, l_0)
    dissipation_rate = nu_val * vorticity**2
    return dissipation_rate * tau / c_p


def get_critical_times(u_0=u_ref, c_sound=c_s, l_0=L_ref, mfp=mfp_water, h_param=h):
    """Calculates critical tau breakdown thresholds for incompressibility, sonic, and continuum."""
    tau_break_Ma = (MACH_INCOMPRESSIBILITY_LIMIT * c_sound / u_0) ** (-1.0 / (0.5 + h_param))
    tau_sonic = (SONIC_MACH_LIMIT * c_sound / u_0) ** (-1.0 / (0.5 + h_param))
    tau_knudsen = (mfp / l_0) ** (1.0 / 0.5)

    tau_range = np.logspace(-30, 0, 1000)
    temps = [temperature_rise(t, u_0=u_0, l_0=l_0, h_param=h_param) for t in tau_range]
    boil_idx = next((i for i, t in enumerate(temps) if t > 100), None)
    tau_boil = float(tau_range[boil_idx]) if boil_idx is not None else None

    return {
        'tau_break_Ma': float(tau_break_Ma),
        'tau_sonic': float(tau_sonic),
        'tau_knudsen': float(tau_knudsen),
        'tau_boil': tau_boil,
    }


def run_audit():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 72)
    print("DIRECTIVE 5: MACH NUMBER DIVERGENCE — PHYSICAL SELF-INVALIDATION")
    print("=" * 72)
    print(f"\n--- Physical Reference Scales (Water at {T}K) ---")
    print(f"  Speed of sound:    c_s = {c_s} m/s")
    print(f"  Kinematic visc:    ν   = {nu:.1e} m²/s")
    print(f"  Initial core:      L₀  = {L_ref*100:.1f} cm")
    print(f"  Reference velocity: u₀  = ν/L₀ = {u_ref:.2e} m/s")
    print(f"  Anisotropy param:  h   = {h}")

    crits = get_critical_times()
    tau_break_Ma = crits['tau_break_Ma']
    tau_sonic = crits['tau_sonic']
    tau_knudsen = crits['tau_knudsen']
    tau_boil = crits['tau_boil']

    print(f"\n--- Critical Times (tau = 1-t, singularity at tau = 0) ---")
    print(f"  Ma = 0.3 (incompressible limit):  tau_break = {tau_break_Ma:.6e}")
    print(f"  Ma = 1.0 (sonic):                 tau_sonic  = {tau_sonic:.6e}")
    print(f"  Kn = 1   (continuum limit):        tau_Kn     = {tau_knudsen:.6e}")
    if tau_boil:
        print(f"  ΔT > 100K (boiling):              tau_boil   = {tau_boil:.6e}")

    print(f"\n--- Mach Number Trajectory ---")
    print(f"  {'tau':>12s}  {'|u| (m/s)':>12s}  {'Ma':>10s}  {'l_r (m)':>12s}  {'Re_angular':>12s}  {'Status':>20s}")
    print(f"  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*12}  {'-'*12}  {'-'*20}")

    tau_samples = [1.0, 1e-2, 1e-5, 1e-8, 1e-10, 1e-12, 1e-15, 1e-18, 1e-20, 1e-25]
    for tau_s in tau_samples:
        u = velocity(tau_s)
        ma = mach_number(tau_s)
        lr = core_radius(tau_s)
        re_a = reynolds_angular(tau_s)
        if ma < 0.3:
            status = "Incompressible"
        elif ma < 1.0:
            status = "Compressible"
        elif lr > mfp_water:
            status = "Supersonic"
        else:
            status = "Sub-molecular"
        print(f"  {tau_s:12.2e}  {u:12.4e}  {ma:10.4e}  {lr:12.4e}  {re_a:12.4e}  {status:>20s}")

    print(f"\n{'=' * 72}")
    print(f"SUMMARY: MACH NUMBER DIVERGENCE ANALYSIS")
    print(f"{'=' * 72}")
    print(f"""
  The OpenAI collapsing vortex core reaches:
  • Ma = 0.3 at τ = {tau_break_Ma:.2e} seconds before singularity
  • Ma = 1.0 at τ = {tau_sonic:.2e} seconds before singularity
  • Core radius reaches molecular scale at τ = {tau_knudsen:.2e}

  CONCLUSION: Navier-Stokes incompressibility fails at τ ≈ {tau_break_Ma:.1e} s.
""")


if __name__ == '__main__':
    run_audit()
