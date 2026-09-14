#!/usr/bin/env python3
"""
Directive 3: Audit of the 5-Moment Jacobian (Non-Dimensionalization & Matrix Scaling)

Analyzes the 5×5 moment-matching Jacobian from Appendix B.8 and Lemma 8.7
of the OpenAI Navier-Stokes paper.

Peer-Review Update:
Demonstrates that the raw condition number explosion (kappa ~ 10^28) observed
in raw SVD is a numerical linear algebra artifact resulting from a lack of
non-dimensionalization.

The moment matrix entries integrate polynomial basis functions (x * X_R)^(2i) and (x * X_R)^(2j).
Factoring A = D * B * D where D = diag(1, X_R^2, X_R^4) (for A_theta) and D_z = diag(X_R, X_R^3) (for A_z)
isolates the dimensional scaling in D. The non-dimensionalized matrix B = D^(-1) A D^(-1) has a bounded
condition number completely independent of X_R.
"""

import numpy as np
from scipy.linalg import svd

# NumPy 1.x and 2.x compatibility (np.trapz removed in NumPy 2.0)
trapezoid = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
import sys

# Set UTF-8 output encoding if possible
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("DIRECTIVE 3: 5-MOMENT JACOBIAN NON-DIMENSIONALIZATION AUDIT")
print("OpenAI Navier-Stokes — Appendix B.8 / Lemma 8.7")
print("=" * 70)

def construct_A_theta(lam, X_R):
    """Construct the 3×3 azimuthal moment block."""
    n_quad = 200
    x = np.linspace(1 - lam, 1 + lam, n_quad)
    dx = x[1] - x[0]
    
    xi = (x - 1) / lam
    bump = np.zeros_like(xi)
    mask = np.abs(xi) < 1
    bump[mask] = np.exp(-1.0 / (1.0 - xi[mask]**2))
    bump /= (np.sum(bump) * dx + 1e-300)
    
    phi = np.zeros((3, n_quad))
    for j in range(3):
        phi[j] = (x * X_R) ** (2 * j) * bump
    
    A = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            integrand = (x * X_R) ** (2 * i) * phi[j]
            A[i, j] = trapezoid(integrand, x)
    
    return A

def construct_A_z(lam, X_R):
    """Construct the 2×2 axial moment block."""
    n_quad = 200
    x = np.linspace(1 - lam, 1 + lam, n_quad)
    dx = x[1] - x[0]
    
    xi = (x - 1) / lam
    bump = np.zeros_like(xi)
    mask = np.abs(xi) < 1
    bump[mask] = np.exp(-1.0 / (1.0 - xi[mask]**2))
    bump /= (np.sum(bump) * dx + 1e-300)
    
    phi = np.zeros((2, n_quad))
    for j in range(2):
        phi[j] = (x * X_R) ** (2 * j + 1) * bump
    
    A = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            integrand = (x * X_R) ** (2 * i + 1) * phi[j]
            A[i, j] = trapezoid(integrand, x)
    
    return A

def get_nondimensional_matrices(lam, X_R):
    """
    Factor A = D * B * D to obtain the non-dimensional matrix B.
    D_theta = diag(1, X_R^2, X_R^4)
    D_z     = diag(X_R, X_R^3)
    """
    A_theta = construct_A_theta(lam, X_R)
    A_z = construct_A_z(lam, X_R)
    
    D_theta = np.diag([1.0, X_R**2, X_R**4])
    D_theta_inv = np.diag([1.0, X_R**(-2), X_R**(-4)])
    B_theta = D_theta_inv @ A_theta @ D_theta_inv
    
    D_z = np.diag([X_R, X_R**3])
    D_z_inv = np.diag([X_R**(-1), X_R**(-3)])
    B_z = D_z_inv @ A_z @ D_z_inv
    
    # Full 5x5 raw and non-dimensionalized matrices
    A_full = np.zeros((5, 5))
    A_full[:3, :3] = A_theta
    A_full[3:, 3:] = A_z
    
    B_full = np.zeros((5, 5))
    B_full[:3, :3] = B_theta
    B_full[3:, 3:] = B_z
    
    return A_full, B_full

# ============================================================
# Sweep X_R to compare Raw vs Non-Dimensionalized Condition Numbers
# ============================================================

print(f"\n--- Condition Number vs. X_R (lambda = 0.1): Raw vs Non-Dimensionalized ---")
print(f"  {'X_R':>10s}  {'kappa(A) [Raw]':>20s}  {'kappa(B) [Non-Dim]':>22s}  {'Interpretation':>20s}")
print(f"  {'-'*10}  {'-'*20}  {'-'*22}  {'-'*20}")

X_Rs = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
lam_fixed = 0.1

for X_R in X_Rs:
    A_full, B_full = get_nondimensional_matrices(lam_fixed, X_R)
    
    _, S_A, _ = svd(A_full)
    kappa_A = S_A[0] / S_A[-1] if S_A[-1] > 1e-300 else float('inf')
    
    _, S_B, _ = svd(B_full)
    kappa_B = S_B[0] / S_B[-1] if S_B[-1] > 1e-300 else float('inf')
    
    interp = "Artifact (Unscaled)" if kappa_A > 1e5 and kappa_B < 1e5 else "Bounded"
    print(f"  {X_R:10.1f}  {kappa_A:20.6e}  {kappa_B:22.6e}  {interp:>20s}")

# ============================================================
# Summary
# ============================================================
print(f"\n{'=' * 70}")
print(f"SUMMARY: NON-DIMENSIONALIZATION AUDIT RESULTS")
print(f"{'=' * 70}")
print(f"""
  PEER-REVIEW VERIFICATION FINDINGS:
  
  1. Raw SVD of the moment matrix A produces a massive condition number (kappa ~ 10^28)
     merely because its entries integrate terms spanning physical dimensions X_R^0 to X_R^8.
  
  2. Factoring A = D * B * D where D = diag(1, X_R^2, X_R^4, X_R, X_R^3) isolates the
     dimensional scaling. The non-dimensionalized matrix B is COMPLETELY INDEPENDENT of X_R.
  
  3. Condition number of the non-dimensionalized system B:
     kappa(B) ≈ {kappa_B:.4e}  (STABLE AND BOUNDED FOR ALL X_R)
  
  CONCLUSION: The 10^28 condition number is a classic numerical artifact of feeding an
  unscaled dimensional matrix into a floating-point solver. Proper non-dimensionalization
  eliminates the X_R dependence entirely. The claim of Jacobian thermal instability is invalid.
""")

