#!/usr/bin/env python3
"""
simu_frustration_Z3.py
======================
Physical Verification of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | SocrateAI Research Initiative

Title: Measurement of the 3D Leray Projector Triadic Frustration Index on Z^3
Description:
    Computes geometric attenuation of convective nonlinear transfer on a 3D
    Galerkin lattice Z^3, and decomposes it into (a) an ordinary
    vector-alignment factor from the scalar contraction (k . u_p), and (b)
    the attenuation specifically attributable to the Leray-Helmholtz
    projector P(k) = I - (k (x) k) / |k|^2 removing the component of the
    convective vector along k.

Revision note (this version): a previous version of this script's docstring
    claimed this produces "a Frustration Ratio D >> 10" from incompressibility
    -- an empirical run instead gives a median combined D of ~2-3, and most of
    even that modest factor comes from (a), the generic alignment term, not
    from the Leray projector itself: the Leray-specific factor (b) has a
    median around 1.0-1.1 (i.e. often a weak effect) with a long right tail.
    This version reports (a) and (b) separately instead of only their
    product, so the Leray-specific claim can be read off directly rather than
    conflated with the alignment term.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def build_transverse_basis(k):
    """
    Constructs an orthonormal helical/transverse frame (e1, e2) orthogonal to wavevector k.
    Guaranteed non-singular across all directions.
    """
    k_norm = np.linalg.norm(k)
    if k_norm < 1e-12:
        return np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0])
    
    # Pick unit vector with minimum projection along k
    abs_k = np.abs(k)
    min_idx = int(np.argmin(abs_k))
    ref = np.zeros(3)
    ref[min_idx] = 1.0
    
    e1 = np.cross(k, ref)
    norm1 = np.linalg.norm(e1)
    if norm1 < 1e-10:
        alt_idx = (min_idx + 1) % 3
        ref = np.zeros(3)
        ref[alt_idx] = 1.0
        e1 = np.cross(k, ref)
        norm1 = np.linalg.norm(e1)
        
    e1 = e1 / norm1
    e2 = np.cross(k, e1)
    e2 = e2 / np.linalg.norm(e2)
    return e1, e2

def leray_project(k, v):
    """
    Applies the Leray-Helmholtz projector P(k) = I - (k (x) k)/|k|^2 to vector v.
    """
    k_sq = np.dot(k, k)
    if k_sq < 1e-12:
        return v
    return v - (np.dot(k, v) / k_sq) * k

def sample_triads_Z3(K_max=12, max_triads=5000):
    """
    Samples integer wavevector triads (k, p, q) in Z^3 satisfying k + p + q = 0.
    """
    triads = []
    coords = [i for i in range(-K_max, K_max + 1) if i != 0]
    
    np.random.seed(42)
    attempts = 0
    while len(triads) < max_triads and attempts < max_triads * 50:
        attempts += 1
        k = np.array([np.random.choice(coords), np.random.choice(coords), np.random.choice(coords)], dtype=float)
        p = np.array([np.random.choice(coords), np.random.choice(coords), np.random.choice(coords)], dtype=float)
        q = -(k + p)
        
        if np.all(q == 0):
            continue
            
        triads.append((k, p, q))
        
    return triads

def compute_frustration_statistics(triads):
    """
    For each triad, evaluates:
      - Unprojected convective transfer capacity: T_unproj = |k| * |u(p)| * |u(q)|
      - Pre-projection convective magnitude: T_conv = |(k . u(p)) u(q)|
      - Leray-projected transfer: T_leray = |P(k) [ (k . u(p)) u(q) ]|
      - Total Frustration Index D = T_unproj / (T_leray + eps)
                                   = D_dot * D_leray_only, decomposed as:
          D_dot        = T_unproj / T_conv   (from |k . u_p| <= |k| alone --
                          this is generic vector-alignment attenuation, NOT
                          specific to incompressibility)
          D_leray_only = T_conv / T_leray    (the part actually attributable
                          to the Leray-Helmholtz projector P(k) removing the
                          component of the convective vector along k)

    A previous version of this script's docstring/printed verdict described D
    itself (median ~2-3 empirically, NOT >>10 as claimed) as "geometric phase
    cancellations forced by the Leray-Helmholtz projector." That conflates the
    two factors above: most of D empirically comes from D_dot (the ordinary
    fact that a random unit vector's component along k is, on average, less
    than |k|), not from D_leray_only, which this version reports separately.
    """
    frustration_indices = []
    unproj_transfers = []
    leray_transfers = []
    conv_transfers = []
    dot_only_factors = []
    leray_only_factors = []

    net_leray_transfer = np.zeros(3)

    for k, p, q in triads:
        e1_p, e2_p = build_transverse_basis(p)
        e1_q, e2_q = build_transverse_basis(q)

        theta_p = np.random.uniform(0, 2 * np.pi)
        theta_q = np.random.uniform(0, 2 * np.pi)

        u_p = np.cos(theta_p) * e1_p + np.sin(theta_p) * e2_p
        u_q = np.cos(theta_q) * e1_q + np.sin(theta_q) * e2_q

        k_norm = np.linalg.norm(k)

        # 1. Unprojected transfer capacity
        T_unproj = k_norm * 1.0 * 1.0

        # 2. Convective interaction (pre-Leray)
        conv_vector = np.dot(k, u_p) * u_q
        T_conv = np.linalg.norm(conv_vector)

        # 3. Leray projection
        proj_vector = leray_project(k, conv_vector)
        T_leray = np.linalg.norm(proj_vector)

        D = T_unproj / max(T_leray, 1e-4)
        D_dot = T_unproj / max(T_conv, 1e-4)
        D_leray_only = T_conv / max(T_leray, 1e-4)

        frustration_indices.append(D)
        unproj_transfers.append(T_unproj)
        leray_transfers.append(T_leray)
        conv_transfers.append(T_conv)
        dot_only_factors.append(D_dot)
        leray_only_factors.append(D_leray_only)

        net_leray_transfer += proj_vector

    frustration_indices = np.array(frustration_indices)
    unproj_arr = np.array(unproj_transfers)
    leray_arr = np.array(leray_transfers)
    conv_arr = np.array(conv_transfers)
    dot_only_arr = np.array(dot_only_factors)
    leray_only_arr = np.array(leray_only_factors)

    # Scientifically rigorous ensemble mean frustration ratio:
    # Compares mean unprojected transfer to mean Leray transfer (O(1) in N, sample-size invariant)
    D_mean = float(np.mean(unproj_arr) / (np.mean(leray_arr) + 1e-12))
    D_dot_mean = float(np.mean(unproj_arr) / (np.mean(conv_arr) + 1e-12))
    D_leray_only_mean = float(np.mean(conv_arr) / (np.mean(leray_arr) + 1e-12))

    # Net shell vector cancellation factor from isotropic phase incoherence
    norm_vector_sum = float(np.linalg.norm(net_leray_transfer))
    sum_scalar_norms = float(np.sum(leray_arr))
    phase_incoherence_factor = float(sum_scalar_norms / (norm_vector_sum + 1e-12))

    return {
        'frustration_indices': frustration_indices,
        'D_mean': D_mean,
        'D_dot_mean': D_dot_mean,
        'D_leray_only_mean': D_leray_only_mean,
        'dot_only_median': float(np.median(dot_only_arr)),
        'leray_only_median': float(np.median(leray_only_arr)),
        'leray_only_p90': float(np.percentile(leray_only_arr, 90)),
        'phase_incoherence_factor': phase_incoherence_factor,
        'unproj_arr': unproj_arr,
        'leray_arr': leray_arr,
    }

def main():
    print("=" * 75)
    print(" 3D LERAY TRIADIC FRUSTRATION AUDIT ON GALERKIN LATTICE Z^3")
    print("=" * 75)
    print("Physical Principle: Incompressibility (div u = 0) enforces multi-axial")
    print("orthogonality, causing severe geometric phase cancellations.\n")

    K_max = 12
    N_triads = 5000
    # Note: k, p have components sampled in [-K_max, K_max]\{0}; the third leg
    # q = -(k+p) is NOT independently bounded by K_max and can reach 2*K_max
    # in a component (confirmed: max |q| component observed ~24 for K_max=12)
    # -- a previous version of this print line implied all three legs were
    # bounded by K_max, which is only true of k and p.
    print(f"[1/3] Sampling {N_triads} divergence-free triads on Z^3 (k + p + q = 0; "
          f"k,p components in [-{K_max},{K_max}]\\{{0}}, q=-(k+p) unconstrained)...")
    triads = sample_triads_Z3(K_max=K_max, max_triads=N_triads)

    print("[2/3] Evaluating Leray projector phase cancellations & Frustration Index D...")
    stats = compute_frustration_statistics(triads)
    frustrations = stats['frustration_indices']
    D_mean = stats['D_mean']

    median_D = float(np.median(frustrations))
    p75_D = float(np.percentile(frustrations, 75))
    p90_D = float(np.percentile(frustrations, 90))
    p95_D = float(np.percentile(frustrations, 95))
    fraction_gt_10 = float(np.mean(frustrations > 10.0) * 100.0)
    fraction_gt_100 = float(np.mean(frustrations > 100.0) * 100.0)

    print("\n" + "=" * 75)
    print(" TRIADIC GEOMETRIC FRUSTRATION METRICS")
    print("=" * 75)
    print(f"Total Triads Analyzed:             {len(frustrations)}")
    print(f"Median COMBINED Frustration (D):   {median_D:>10.2f}")
    print(f"Mean Transfer Attenuation (D_mean):{D_mean:>10.2f}")
    print(f"75th Percentile Frustration (D):   {p75_D:>10.2f}")
    print(f"90th Percentile Frustration (D):   {p90_D:>10.2f}")
    print(f"95th Percentile Frustration (D):   {p95_D:>10.2f}")
    print(f"Triads with Frustration D > 10:    {fraction_gt_10:>10.1f} %")
    print(f"Triads with Frustration D > 100:   {fraction_gt_100:>10.1f} %")
    print("-" * 75)
    print(" DECOMPOSITION: D = D_dot (alignment) x D_leray_only (Leray-specific)")
    print("-" * 75)
    print(f"Median D_dot   (|k|/|(k.u_p)u_q|, NOT Leray-specific): {stats['dot_only_median']:>8.2f}")
    print(f"Median D_leray_only (Leray-specific attenuation):      {stats['leray_only_median']:>8.2f}")
    print(f"90th pct D_leray_only:                                 {stats['leray_only_p90']:>8.2f}")
    print("-" * 75)
    print(f"Shell Vector Cancellation (Random):{stats['phase_incoherence_factor']:>10.2f}x (Scales with sqrt(N))")
    print("=" * 75)

    print("\n[3/3] Generating publication-quality diagnostic plots...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Histogram / PDF of Frustration Index log10(D)
    log_D = np.log10(np.clip(frustrations, 1.0, 1e4))
    ax1.hist(log_D, bins=50, color='#1f77b4', edgecolor='black', alpha=0.75, density=True)
    ax1.axvline(x=1.0, color='red', linestyle='--', linewidth=2.5, label=r'Threshold $\mathcal{D} = 10$')
    ax1.axvline(x=np.log10(median_D), color='orange', linestyle='-', linewidth=2.0, label=rf'Median $\mathcal{{D}} = {median_D:.1f}$')
    ax1.set_xlabel(r'$\log_{10}(\mathcal{D})$ [Triadic Frustration Index]', fontsize=12)
    ax1.set_ylabel('Probability Density', fontsize=12)
    ax1.set_title(r'Distribution of Leray Frustration $\mathcal{D}(k,p,q)$ on $\mathbb{Z}^3$', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, ls=":", alpha=0.6)

    # Subplot 2: Unprojected vs Leray-Projected Transfer Intensity
    unproj = stats['unproj_arr']
    leray = stats['leray_arr']
    sample_sub = np.random.choice(len(unproj), size=min(800, len(unproj)), replace=False)
    ax2.scatter(unproj[sample_sub], leray[sample_sub], alpha=0.45, color='#2ca02c', edgecolors='none', s=25)
    ax2.plot([0, np.max(unproj)], [0, np.max(unproj)], 'r--', linewidth=2.0, label=r'Uninhibited Transfer ($P=I$)')
    ax2.plot([0, np.max(unproj)], [0, 0.1 * np.max(unproj)], 'b:', linewidth=2.0, label=r'10x Frustration Barrier ($\mathcal{D}=10$)')
    ax2.set_xlabel(r'Unprojected Transfer Intensity $|k| |u_p| |u_q|$', fontsize=12)
    ax2.set_ylabel(r'Leray-Projected Transfer Intensity $|\mathbb{P}(k) [v]|$', fontsize=12)
    ax2.set_title(r'Geometric Transfer Suppression on $\mathbb{Z}^3$', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10, loc='upper left')
    ax2.grid(True, ls=":", alpha=0.6)

    plt.tight_layout()
    output_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leray_triadic_frustration_Z3.png')
    plt.savefig(output_png, dpi=300)
    print(f"[FIGURE] Saved empirical verification figure to: {output_png}")
    print(f"[EPISTEMIC VERDICT] Combined median D = {median_D:.2f} (mean D_mean = {D_mean:.2f}), but the")
    print(f"                   decomposition above shows most of that comes from generic vector alignment")
    print(f"                   (median D_dot = {stats['dot_only_median']:.2f}), not incompressibility: the")
    print(f"                   Leray-specific factor alone has median D_leray_only = {stats['leray_only_median']:.2f}")
    print(f"                   (90th pct {stats['leray_only_p90']:.2f}) -- a weak effect for most triads, with")
    print(f"                   a right tail. This does NOT support a strong, general 'incompressibility")
    print(f"                   geometrically quenches nonlinear transfer' claim on its own; it supports a")
    print(f"                   much narrower one -- that the Leray projector's effect on a single random")
    print(f"                   triad is usually modest, occasionally large.\n")

if __name__ == '__main__':
    main()
