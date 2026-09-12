#!/usr/bin/env python3
"""
Directive 5: Mach Number Divergence — Physical Self-Invalidation

Tracks the local Mach number Ma = |u|/c_s of the OpenAI collapsing vortex
core as tau -> 0, demonstrating that the incompressibility assumption
(Ma << 1) breaks down BEFORE the mathematical blowup time.
"""

import numpy as np
import os

# ============================================================
# Physical Constants (Water at 300K)
# ============================================================
c_s = 1500.0       # Speed of sound in water (m/s)
nu = 1.0e-6         # Kinematic viscosity of water (m²/s)
rho = 1000.0        # Density (kg/m³)
k_B = 1.381e-23     # Boltzmann constant (J/K)
T = 300.0           # Temperature (K)

# Anisotropy parameter (from the paper: h < 1/100)
h = 0.005           # h = 1/200

# ============================================================
# Reference Scales
# ============================================================
# The OpenAI construction works in dimensionless units.
# We must choose a physical reference scale.
#
# The vortex core has initial radial scale l_r(0) ~ tau(0)^{1/2}
# At tau = 1 (t = 0), we set l_r ~ L_ref (some macroscopic length).
# For a laboratory vortex: L_ref ~ 0.01 m (1 cm initial core radius)
L_ref = 0.01  # meters

# Reference velocity from the paper's scaling at tau = 1:
# u_ref = nu / L_ref (viscous velocity scale)
u_ref = nu / L_ref  # ~ 10^{-4} m/s (very slow initially)
print("=" * 72)
print("DIRECTIVE 5: MACH NUMBER DIVERGENCE — PHYSICAL SELF-INVALIDATION")
print("=" * 72)
print(f"\n--- Physical Reference Scales (Water at {T}K) ---")
print(f"  Speed of sound:    c_s = {c_s} m/s")
print(f"  Kinematic visc:    ν   = {nu:.1e} m²/s")
print(f"  Initial core:      L₀  = {L_ref*100:.1f} cm")
print(f"  Reference velocity: u₀  = ν/L₀ = {u_ref:.2e} m/s")
print(f"  Anisotropy param:  h   = {h}")

# ============================================================
# Velocity and Mach number as functions of tau
# ============================================================
# Dominant velocity: u_theta ~ u_ref * tau^{-1/2 - h}
# This is the azimuthal velocity at the vortex core edge
# Mach number: Ma = u_theta / c_s

def velocity(tau):
    """Peak velocity at the vortex core edge."""
    return u_ref * tau ** (-0.5 - h)

def mach_number(tau):
    """Local Mach number."""
    return velocity(tau) / c_s

def core_radius(tau):
    """Radial scale of the vortex core."""
    return L_ref * tau ** 0.5

def reynolds_angular(tau):
    """Angular Reynolds number ~ u_theta * l_r / nu."""
    return velocity(tau) * core_radius(tau) / nu

def temperature_rise(tau):
    """
    Local temperature rise from viscous dissipation.
    Delta_T ~ nu * |curl u|^2 * tau / (rho * c_p)
    |curl u| ~ u_theta / l_r
    c_p for water ~ 4186 J/(kg·K)
    """
    c_p = 4186.0  # J/(kg·K)
    vorticity = velocity(tau) / core_radius(tau)
    dissipation_rate = nu * vorticity**2  # W/m³/rho
    delta_T = dissipation_rate * tau / c_p
    return delta_T

# ============================================================
# Find critical times
# ============================================================
# Ma = 0.3 threshold (incompressibility breaks)
# u_ref * tau^{-0.5-h} / c_s = 0.3
# tau^{-0.5-h} = 0.3 * c_s / u_ref
# tau = (0.3 * c_s / u_ref)^{-1/(0.5+h)}

Ma_threshold = 0.3
tau_break_Ma = (Ma_threshold * c_s / u_ref) ** (-1.0 / (0.5 + h))

# Ma = 1.0 (sonic)
tau_sonic = (1.0 * c_s / u_ref) ** (-1.0 / (0.5 + h))

# Knudsen number = mean_free_path / l_r = 1 (continuum breaks)
# Mean free path in water ~ 3e-10 m (intermolecular distance)
mfp_water = 3.0e-10  # meters
tau_knudsen = (mfp_water / L_ref) ** (1.0 / 0.5)

# Temperature: Delta_T > 100K (boiling)
# Find numerically
tau_range = np.logspace(-30, 0, 10000)
temps = [temperature_rise(t) for t in tau_range]
boil_idx = next((i for i, t in enumerate(temps) if t > 100), None)
tau_boil = tau_range[boil_idx] if boil_idx else None

print(f"\n--- Critical Times (tau = 1-t, singularity at tau = 0) ---")
print(f"  Ma = 0.3 (incompressible limit):  tau_break = {tau_break_Ma:.6e}")
print(f"  Ma = 1.0 (sonic):                 tau_sonic  = {tau_sonic:.6e}")
print(f"  Kn = 1   (continuum limit):        tau_Kn     = {tau_knudsen:.6e}")
if tau_boil:
    print(f"  ΔT > 100K (boiling):              tau_boil   = {tau_boil:.6e}")

print(f"\n  Physical time remaining before singularity:")
print(f"    At Ma = 0.3: t_remaining = {tau_break_Ma:.6e} seconds")
print(f"    At sonic:    t_remaining = {tau_sonic:.6e} seconds")

# ============================================================
# Generate the Mach number trajectory
# ============================================================
print(f"\n--- Mach Number Trajectory ---")
tau_points = np.logspace(-25, 0, 200)
ma_points = [mach_number(t) for t in tau_points]
vel_points = [velocity(t) for t in tau_points]
re_points = [reynolds_angular(t) for t in tau_points]

# Table of key values
print(f"\n  {'tau':>12s}  {'|u| (m/s)':>12s}  {'Ma':>10s}  {'l_r (m)':>12s}  {'Re_angular':>12s}  {'Status':>20s}")
print(f"  {'-'*12}  {'-'*12}  {'-'*10}  {'-'*12}  {'-'*12}  {'-'*20}")

tau_samples = [1.0, 1e-2, 1e-5, 1e-8, 1e-10, 1e-12, 1e-15, 1e-18, 1e-20, 1e-25]
for tau in tau_samples:
    u = velocity(tau)
    ma = mach_number(tau)
    lr = core_radius(tau)
    re_a = reynolds_angular(tau)
    
    if ma < 0.3:
        status = "✅ Incompressible"
    elif ma < 1.0:
        status = "⚠️  Compressible"
    elif lr > mfp_water:
        status = "🔴 Supersonic"
    else:
        status = "💀 Sub-molecular"
    
    print(f"  {tau:12.2e}  {u:12.4e}  {ma:10.4e}  {lr:12.4e}  {re_a:12.4e}  {status}")

# ============================================================
# ASCII Plot: Mach Number vs tau
# ============================================================
print(f"\n--- Mach Number vs. Time to Singularity (log-log) ---")
width = 65
height = 22

log_tau = [np.log10(t) for t in tau_points if mach_number(t) > 1e-10]
log_ma = [np.log10(mach_number(t)) for t in tau_points if mach_number(t) > 1e-10]

x_min, x_max = min(log_tau), max(log_tau)
y_min, y_max = -5, max(log_ma)

grid = [[' '] * width for _ in range(height)]

# Plot the Ma curve
for x, y in zip(log_tau, log_ma):
    col = int((x - x_min) / (x_max - x_min) * (width - 1))
    row = height - 1 - int((y - y_min) / (y_max - y_min) * (height - 1))
    col = max(0, min(width-1, col))
    row = max(0, min(height-1, row))
    grid[row][col] = '●'

# Mark Ma = 0.3 line
ma_03_row = height - 1 - int((np.log10(0.3) - y_min) / (y_max - y_min) * (height - 1))
if 0 <= ma_03_row < height:
    for c in range(width):
        if grid[ma_03_row][c] == ' ':
            grid[ma_03_row][c] = '─'

# Mark Ma = 1.0 line
ma_1_row = height - 1 - int((0 - y_min) / (y_max - y_min) * (height - 1))
if 0 <= ma_1_row < height:
    for c in range(width):
        if grid[ma_1_row][c] == ' ':
            grid[ma_1_row][c] = '═'

print(f"  log₁₀(Ma) ^")
for i in range(height):
    y_label = y_max - (y_max - y_min) * i / (height - 1)
    label = ""
    if i == ma_03_row:
        label = " ← Ma=0.3 (INCOMPRESSIBLE LIMIT)"
    elif i == ma_1_row:
        label = " ← Ma=1.0 (SONIC BARRIER)"
    if i % 5 == 0:
        print(f"  {y_label:6.1f} |{''.join(grid[i])}{label}")
    else:
        print(f"         |{''.join(grid[i])}{label}")
print(f"         +{'-' * width}> log₁₀(τ)")
print(f"          {x_min:.0f}{' ' * (width - 5)}{x_max:.0f}")

# ============================================================
# Summary
# ============================================================
print(f"\n{'=' * 72}")
print(f"SUMMARY: MACH NUMBER DIVERGENCE ANALYSIS")
print(f"{'=' * 72}")
print(f"""
  The OpenAI collapsing vortex core reaches:
  
  • Ma = 0.3 at τ = {tau_break_Ma:.2e} seconds before singularity
    → Incompressibility assumption FAILS
    → Must switch to COMPRESSIBLE Navier-Stokes
    
  • Ma = 1.0 at τ = {tau_sonic:.2e} seconds before singularity
    → SONIC BARRIER — shock waves form
    → Entropy production becomes dominant
    
  • Core radius reaches molecular scale at τ = {tau_knudsen:.2e}
    → CONTINUUM HYPOTHESIS FAILS
    → Must use Boltzmann kinetic theory

  🔴 CONCLUSION: The mathematical singularity at τ = 0 is physically
  unreachable. The Navier-Stokes equations self-invalidate at τ ≈ {tau_break_Ma:.1e}
  when the Mach number exceeds 0.3. The compressible equations would
  generate acoustic radiation and thermal shocks that arrest the collapse.
  
  The AI's singularity exists only in the mathematical limit of a PDE
  that has ceased to describe the physical system it was derived from.
""")
