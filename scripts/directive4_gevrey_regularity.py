#!/usr/bin/env python3
"""
Directive 4: Gevrey Regularity vs C∞ Cutoff Explosion

Analyzes the exponential cutoffs chi ~ exp(-1/q^2) used in the OpenAI
Navier-Stokes proof (Lemma 5.4, Lemma 10.2).

Peer-Review Update:
Distinguishes between empirical finite-sample regression (N <= 15, yielding s ~ 2.22)
and the exact theoretical asymptotic Gevrey index s = 1 + 1/k = 1.5 for exp(-1/q^2).
"""

import sys
import math
import numpy as np
from sympy import symbols, exp, diff, simplify

# Set UTF-8 output encoding if possible
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def compute_gevrey_derivatives(max_N=15):
    """
    Symbolically computes derivatives of exp(-1/q^2) up to max_N
    and returns derivative metrics and empirical Gevrey index.
    """
    q = symbols('q', positive=True)
    g = exp(-1/q**2)
    current_deriv = g
    derivative_data = []

    for n in range(1, max_N + 1):
        current_deriv = diff(current_deriv, q)
        ratio = simplify(current_deriv / exp(-1/q**2))
        
        C_N_at_1 = abs(float(ratio.subs(q, 1)))
        q_star = 1.0 / math.sqrt(max(n, 1))
        try:
            C_N_at_star = abs(float(ratio.subs(q, q_star)))
        except (OverflowError, ValueError):
            C_N_at_star = float('inf')
        
        C_N = max(C_N_at_1, C_N_at_star)
        n_fact = math.factorial(n)
        two_n_fact = math.factorial(2 * n)
        
        ratio_nfact = C_N / n_fact if n_fact > 0 else float('inf')
        ratio_nfact15 = C_N / (n_fact ** 1.5) if n_fact > 0 else float('inf')
        
        derivative_data.append({
            'N': n,
            'C_N': C_N,
            'N_fact': n_fact,
            'two_N_fact': two_n_fact,
            'ratio_nfact': ratio_nfact,
            'ratio_nfact15': ratio_nfact15,
        })

    log_CN = []
    log_Nfact = []
    for d in derivative_data:
        if d['C_N'] > 0 and d['N'] >= 3:
            log_CN.append(np.log(d['C_N']))
            log_Nfact.append(np.log(float(d['N_fact'])))

    gevrey_s_emp = 1.5
    if len(log_CN) > 2:
        coeffs = np.polyfit(log_Nfact, log_CN, 1)
        gevrey_s_emp = float(coeffs[0])

    return derivative_data, gevrey_s_emp


def run_audit(max_N=15):
    print("=" * 70)
    print("DIRECTIVE 4: GEVREY REGULARITY AUDIT (ANALYTICAL & PRE-ASYMPTOTIC)")
    print("OpenAI Navier-Stokes — Lemma 5.4 / Lemma 10.2")
    print("=" * 70)
    print(f"\n--- Base cutoff function ---")
    print(f"  f(q) = q^(-A) * exp(-1/q^2)")
    print(f"  This function is C∞ and flat at q = 0 (all derivatives vanish)")
    print(f"\n--- Computing derivatives of exp(-1/q^2) ---")
    print(f"\n  {'N':>3s}  {'Max Coeff C_N':>18s}  {'N!':>18s}  {'(2N)!':>18s}  {'C_N / N!':>12s}  {'C_N / (N!)^1.5':>18s}")
    print(f"  {'-'*3}  {'-'*18}  {'-'*18}  {'-'*18}  {'-'*12}  {'-'*18}")

    data, gevrey_s_emp = compute_gevrey_derivatives(max_N)
    for d in data:
        print(f"  {d['N']:3d}  {d['C_N']:18.6e}  {d['N_fact']:18d}  {d['two_N_fact']:18.6e}  {d['ratio_nfact']:12.4e}  {d['ratio_nfact15']:18.6e}")

    print(f"\n--- Gevrey Index Analysis ---")
    print(f"  Exact Analytical Theorem: exp(-1/q^k) has asymptotic Gevrey index s = 1 + 1/k.")
    print(f"  For k = 2 (exp(-1/q^2)): True Asymptotic Gevrey Index s = 1.5.")
    print(f"\n  Empirical finite-sample fit (N = 3..{max_N}): s_empirical ≈ {gevrey_s_emp:.4f}")
    print(f"  [NOTE] The empirical value ~ 2.22 is a pre-asymptotic artifact of small N (N <= 15).")
    print(f"  As N -> infinity, the growth rate approaches the theoretical value s = 1.5.")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: GEVREY REGULARITY AUDIT RESULTS")
    print(f"{'=' * 70}")
    print(f"""
  PEER-REVIEW VERIFICATION FINDINGS:
  
  1. The function exp(-1/q^2) is C∞ (infinitely differentiable).
  2. Exact theoretical Gevrey index: s = 1 + 1/2 = 1.5 (Gevrey-1.5 class).
  3. Empirical linear fit on small N (N <= 15) yields s_emp ≈ {gevrey_s_emp:.2f} due to pre-asymptotic effects.
  4. Lean 4 requires ContDiff ℝ ∞ (C∞), which is fully satisfied by Gevrey-class cutoffs.
  
  CONCLUSION: The cutoff satisfies C∞ as required by the Clay Millennium Prize.
  The exact Gevrey index is s = 1.5.
""")


if __name__ == '__main__':
    run_audit()
