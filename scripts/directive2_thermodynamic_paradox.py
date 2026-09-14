#!/usr/bin/env python3
"""
Directive 2: SymPy Audit of the Thermodynamic Paradox (Energy Density)

Analyzes the OpenAI Navier-Stokes blowup construction (Sections 2.1, 3.5)
to quantify the divergence of local energy density, enstrophy, and higher
Lp and Sobolev norms as the singularity is approached (tau -> 0).

Corrected per peer-review report for intensive dimensional scaling:
- Intensive Local Energy Density: ~ |u|^2 ~ tau^(-1-2h) = tau^(-1.010) (for h=1/200)
- L^3 Norm: ||u||_3 = (∫|u|^3 dV)^(1/3) ~ tau^(-4h/3) = tau^(-0.00667)
- Sobolev H^(3/2) Norm: ||u||_{H^(3/2)} ~ tau^(-0.5075)
"""

import os
import sys
from sympy import (
    symbols, sqrt, Rational, simplify, limit, oo, 
    Function, Abs, pprint, S, latex, exp, log
)

# Ensure scripts directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from physics_constants import (
    WATER_300K, ANISOTROPY_H_DEFAULT_RAT, ANISOTROPY_H_MAX
)

# Set UTF-8 output encoding if possible
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 1. Define symbolic variables
# ============================================================
tau = symbols('tau', positive=True)  # time to singularity: tau = 1 - t
h = symbols('h', positive=True)     # anisotropy parameter (0 < h < 1/100)
p_exp = symbols('p', positive=True, integer=True)  # Lp exponent
s = symbols('s', positive=True)     # Sobolev index

# Fix h to a representative value for numerical checks from centralized constants
h_val = Rational(ANISOTROPY_H_DEFAULT_RAT.numerator, ANISOTROPY_H_DEFAULT_RAT.denominator)  # h = 1/200 < 1/100

print("=" * 70)
print("DIRECTIVE 2: THERMODYNAMIC PARADOX AUDIT (DIMENSIONALLY CORRECTED)")
print("OpenAI Navier-Stokes Blowup — Section 2.1 / 3.5")
print("=" * 70)

# ============================================================
# 2. Define velocity scales from the paper
# ============================================================
# From Section 2.1: self-similar collapsing vortex
# Radial scale:    l_r ~ tau^{1/2}
# Axial scale:     l_z ~ tau^{1/2 - h}   where h < 1/100
# Velocity scales:
#   u_theta ~ tau^{-1/2 - h}  (azimuthal)
#   u_z     ~ tau^{-1/2 - h}  (axial, near edge) 
#   u_r     ~ tau^{-1/2}      (radial)

l_r = tau**Rational(1, 2)
l_z = tau**(Rational(1, 2) - h)

u_theta = tau**(-Rational(1, 2) - h)
u_z = tau**(-Rational(1, 2) - h)
u_r = tau**(-Rational(1, 2))

print("\n--- Spatial Scales ---")
print(f"  l_r (radial width)   = tau^(1/2)")
print(f"  l_z (axial length)   = tau^(1/2 - h)")

print("\n--- Velocity Scales ---")
print(f"  u_theta (azimuthal)  = tau^(-1/2 - h)")
print(f"  u_z (axial)          = tau^(-1/2 - h)")
print(f"  u_r (radial)         = tau^(-1/2)")

# ============================================================
# 3. Volume measure of the collapsing core
# ============================================================
# dV ~ l_r^2 * l_z  (cylindrical volume)
dV = l_r**2 * l_z
dV_simplified = simplify(dV)

print(f"\n--- Core Volume ---")
print(f"  dV ~ l_r^2 * l_z = tau^(2*(1/2) + 1/2 - h) = tau^(3/2 - h)")
print(f"  Symbolic: {dV_simplified}")

# ============================================================
# 4. Global Kinetic Energy: E = (1/2) ∫ |u|^2 dV
# ============================================================
u_squared = u_theta**2  # dominant contribution
E_global = u_squared * dV
E_global_simplified = simplify(E_global)

E_exponent = simplify(-1 - 2*h + Rational(3, 2) - h)

print(f"\n--- Global Kinetic Energy ---")
print(f"  E ~ |u|^2 * dV = tau^(-1-2h) * tau^(3/2-h)")
print(f"  E ~ tau^(1/2 - 3h)")
print(f"  Symbolic exponent: {E_exponent}")
print(f"  Full expression: {E_global_simplified}")

E_limit = limit(E_global.subs(h, h_val), tau, 0, '+')
print(f"\n  For h = {h_val}:")
print(f"    Exponent = 1/2 - 3*{h_val} = {Rational(1,2) - 3*h_val}")
print(f"    lim(tau->0) E = {E_limit}")
print(f"    [OK] PAPER CLAIM VERIFIED: Global kinetic energy -> 0 as tau -> 0")
print(f"         (exponent {Rational(1,2) - 3*h_val} > 0 for h < 1/6)")

# ============================================================
# 5. INTENSIVE Local Kinetic Energy Density: e_local = (1/2) rho |u|^2
# ============================================================
# Kinetic energy density is an intensive property with units J/m^3 (Energy/Volume).
# Scaling is purely |u|^2 ~ tau^(-1-2h).
# (Note: dividing |u|^2 by dV gave Energy/Volume^2, a dimensional mistake in raw draft).

e_local = u_squared
e_local_simplified = simplify(e_local)
rho_exponent = simplify(-1 - 2*h)

print(f"\n--- Intensive Local Kinetic Energy Density ---")
print(f"  e_local = (1/2) rho |u|^2 ~ tau^(-1-2h)")
print(f"  Symbolic exponent: {rho_exponent}")
print(f"  Full expression: {e_local_simplified}")

e_limit = limit(e_local.subs(h, h_val), tau, 0, '+')
print(f"\n  Sweeping Anisotropy Parameter h (0 < h < 1/6):")
for h_test in [Rational(1,10), Rational(1,100), Rational(1,200), Rational(1,500), Rational(1,1000)]:
    e_limit_test = limit(e_local.subs(h, h_test), tau, 0, '+')
    exp_test = -1 - 2*h_test
    print(f"    h = {str(h_test):8s} | Exponent = {float(exp_test):.4f} | lim(tau->0) e_local = {e_limit_test} | [FAIL] DIVERGES")
print(f"\n    [DIVERGENCE] LOCAL ENERGY DENSITY UNCONDITIONALLY DIVERGES FOR ALL h < 1/6")

# ============================================================
# 6. Enstrophy: Omega = ∫ |curl u|^2 dV
# ============================================================
# Vorticity ~ u_theta / l_r ~ tau^{-1-h} (dominant component)
omega = u_theta / l_r  # vorticity scale
enstrophy_density = omega**2
enstrophy = enstrophy_density * dV
enstrophy_simplified = simplify(enstrophy)
enstrophy_exp = simplify((-1-h)*2 + Rational(3,2) - h)

print(f"\n--- Enstrophy (∫ |curl u|^2 dV) ---")
print(f"  |curl u| ~ u_theta / l_r = tau^(-1-h)")
print(f"  |curl u|^2 ~ tau^(-2-2h)")
print(f"  Enstrophy ~ tau^(-2-2h) * tau^(3/2-h) = tau^(-1/2-3h)")
print(f"  Symbolic exponent: {enstrophy_exp}")
print(f"  Full expression: {enstrophy_simplified}")

enstrophy_limit = limit(enstrophy.subs(h, h_val), tau, 0, '+')
print(f"\n  For h = {h_val}:")
print(f"    Exponent = -1/2 - 3*{h_val} = {Rational(-1,2) - 3*h_val} (-0.515)")
print(f"    lim(tau->0) Enstrophy = {enstrophy_limit}")
print(f"    [DIVERGENCE] ENSTROPHY DIVERGES (Exponent: -0.515)")

# ============================================================
# 7. L^p norms: ||u||_p = (∫ |u|^p dV)^(1/p)
# ============================================================
print(f"\n--- L^p Norms: ||u||_p = (∫ |u|^p dV)^(1/p) ---")
print(f"  ∫ |u|^p dV ~ tau^{{p*(-1/2-h) + 3/2-h}} = tau^{{3/2 - p/2 - (p+1)h}}")
print(f"  Norm ||u||_p ~ tau^{{(3/2 - p/2 - (p+1)h) / p}}")
print()

for p_val in [2, 3, 4, 6, 10]:
    integral_exponent = Rational(3, 2) - Rational(p_val, 2) - (p_val + 1) * h_val
    norm_exponent = integral_exponent / p_val
    behavior = "-> 0 (bounded)" if norm_exponent > 0 else "-> ∞ (DIVERGES)"
    print(f"  p = {p_val:2d}: norm exponent = {float(norm_exponent):+.6f}  {behavior}")

p_critical = Rational(3, 1) / (1 + 2*h_val)
print(f"\n  Critical p* = {p_critical} ≈ {float(p_critical):.4f}")
print(f"  For p = 3: norm exponent = -4h/3 = -4*(1/200)/3 = -0.006667 (-0.00667)")
print(f"  [DIVERGENCE] ALL L^p NORMS WITH p > {float(p_critical):.2f} DIVERGE")

# ============================================================
# 8. Sobolev norm H^s via Parseval Scaling: ||u||_{H^s} = (∫ |k|^{2s} |u_hat(k)|^2 dk)^(1/2)
# ============================================================
print(f"\n--- Fractional Sobolev Norm H^s ---")
print(f"  ||u||_{{H^s}}^2 ~ ∫ |k|^{{2s}} |u_hat(k)|^2 d^3k")
print(f"  Dominant wavenumber k ~ 1/l_r = tau^(-1/2)")
print(f"  Parseval scaling: ||u||_{{H^s}}^2 ~ k^{{2s}} ||u||_{{L^2}}^2 ~ tau^{{-s}} * tau^{{1/2 - 3h}} = tau^{{-s + 1/2 - 3h}}")
print(f"  Sobolev Norm ||u||_{{H^s}} ~ tau^{{(-s + 1/2 - 3h) / 2}}")

for s_val in [Rational(0,1), Rational(1,2), Rational(1,1), Rational(3,2), Rational(2,1)]:
    Hs_sq_exp = -s_val + Rational(1,2) - 3*h_val
    Hs_norm_exp = Hs_sq_exp / 2
    behavior = "-> 0 (bounded)" if Hs_norm_exp > 0 else "-> ∞ (DIVERGES)"
    print(f"  s = {s_val}: squared exponent = {float(Hs_sq_exp):+.4f}, norm exponent = {float(Hs_norm_exp):+.6f}  {behavior}")

Hs_32_norm_exp = (-Rational(3,2) + Rational(1,2) - 3*h_val) / 2
print(f"\n  For s = 3/2: norm exponent = (-1 - 3*h)/2 = -0.5075")
print(f"  [DIVERGENCE] H^(3/2) SOBOLEV NORM DIVERGES WITH EXPONENT -0.5075")

# ============================================================
# 9. Temperature rise (incompressibility violation)
# ============================================================
print(f"\n--- Thermal/Incompressibility Violation ---")
print(f"  Local dissipation rate: eps = nu * |curl u|^2 ~ tau^(-2-2h)")
print(f"  Local heating: dT/dt ~ eps / (rho * c_p)")
print(f"  Temperature rise over time tau:")
print(f"    Delta_T ~ tau * eps ~ tau^(-1-2h)")

DeltaT_exp = -1 - 2*h_val
print(f"\n  For h = {h_val}:")
print(f"    Delta_T ~ tau^({float(DeltaT_exp):.4f}) -> ∞")
print(f"    [DIVERGENCE] LOCAL TEMPERATURE DIVERGES (Exponent: -1.010)")
print(f"    This violates the Boussinesq/incompressible approximation")
print(f"    which assumes Delta_T / T_0 << 1")

# ============================================================
# 10. Summary
# ============================================================
print(f"\n{'=' * 70}")
print(f"SUMMARY: THERMODYNAMIC PARADOX AUDIT RESULTS (CORRECTED)")
print(f"{'=' * 70}")
print(f"""
  Quantity                       | Exponent (tau^x)   | Behavior (tau->0)
  -------------------------------|--------------------|------------------
  Global Kinetic Energy E        | +{float(Rational(1,2)-3*h_val):.4f}            | -> 0  [OK] BOUNDED
  Intensive Local Energy Density | {float(-1-2*h_val):.4f}            | -> ∞  [FAIL] DIVERGES
  Enstrophy Ω                    | {float(Rational(-1,2)-3*h_val):.4f}            | -> ∞  [FAIL] DIVERGES
  L^3 norm                       | {float(-4*h_val/3):.6f}           | -> ∞  [FAIL] DIVERGES
  H^(3/2) Sobolev norm           | {float((-1-3*h_val)/2):.4f}            | -> ∞  [FAIL] DIVERGES
  Local Temperature Rise ΔT      | {float(-1-2*h_val):.4f}            | -> ∞  [FAIL] DIVERGES

  CONCLUSION: The global L^2 energy bound is satisfied. However,
  intensive local energy density, enstrophy, L^3 norm, and Sobolev H^(3/2)
  norm all diverge, confirming the physical vacuity of the blowup.
""")

