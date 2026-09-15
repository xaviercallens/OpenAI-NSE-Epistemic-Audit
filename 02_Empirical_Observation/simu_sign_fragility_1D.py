#!/usr/bin/env python3
"""
simu_sign_fragility_1D.py
=========================
Physical Verification of the OpenAI Navier-Stokes/Euler Singularity
MechanicaFluidorum Program | SocrateAI Research Initiative

Title: Numerical Demonstration of Dyadic Cascade Sign Fragility
Description:
    Demonstrates that finite-time blowup in scalar dyadic shell models
    (the structural paradigm underlying manufactured 1D blowups) requires
    phase-coherent (same-sign) triad interactions, and asks how robust the
    resulting cascade is to phase perturbation.

    Rigorous Integration:
    Uses SciPy's implicit Radau ODE solver, designed for stiff systems, so
    that whatever a run shows is a genuine consequence of the ODE's own
    dynamics, not an artifact of numerical dissipation.

Revision note (this version):
    A previous version of this script compared the solver's own printed
    per-case result against a fixed absolute enstrophy threshold (1e15) to
    decide "BLOW-UP" vs "ARRESTED" vs "REGULAR" -- but then printed a summary
    table with those three labels HARD-CODED, independent of what the solver
    actually returned. Separately, that threshold was mathematically
    unreachable for ANY phase configuration with N=22 shells: this model
    exactly conserves total energy sum(u_n^2) in the inviscid limit for ANY
    phases (a telescoping identity in the transfer terms, not something that
    requires coherence), so enstrophy = sum(lambda_n^2 u_n^2) is hard-bounded
    by lambda_max^2 * E0 = 4^(N-1) * u0(0)^2 ~= 4.4e12 for N=22 -- the
    solver could never cross 1e15 regardless of what the phases were.

    This version instead (a) derives every printed status from what the
    solver actually returns, and (b) replaces the unreachable absolute
    threshold with a reachable, physically meaningful diagnostic: the
    fraction of total enstrophy concentrated in the terminal (highest-n)
    shell. In a truncated shell model, a coherent cascade genuinely runs to
    the truncation boundary in finite time (verified numerically below); that
    is the finite-N analogue of the untruncated model's ultraviolet blow-up.

    It also fixes two things the previous "sign fragility" framing didn't
    actually test: the "local phase disruption" case previously used
    theta_6 = pi/2, which sets cos(theta_6) = 0 and completely SEVERS shell
    6 from the cascade -- that demonstrates decoupling, not sensitivity to a
    generic perturbation, so this version adds a genuinely partial
    perturbation for contrast. And the "turbulent phase jitter" case
    previously sampled phases from [-pi/3, pi/3], where cos(theta) is always
    positive -- i.e. no interaction ever actually changed SIGN, despite the
    script's title -- this version widens that range so some transfers can
    and do flip sign.
"""

import os
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def dyadic_rhs(t, u, phases, lambdas, N, nu):
    """
    RHS for the energy-conserving dyadic shell model with inter-shell phase angles:
      d u_n / dt = lambda_n cos(theta_n) u_{n-1}^2 - lambda_{n+1} cos(theta_{n+1}) u_n u_{n+1} - nu * lambda_n^2 * u_n
    """
    du = np.zeros(N)

    # Boundary n = 0
    du[0] = - lambdas[1] * np.cos(phases[1]) * u[0] * u[1] - nu * (lambdas[0]**2) * u[0]

    # Inner shells 1 <= n < N-1
    for n in range(1, N - 1):
        transfer_in = lambdas[n] * np.cos(phases[n]) * (u[n-1]**2)
        transfer_out = lambdas[n+1] * np.cos(phases[n+1]) * u[n] * u[n+1]
        visc = nu * (lambdas[n]**2) * u[n]
        du[n] = transfer_in - transfer_out - visc

    # Boundary n = N - 1
    du[N-1] = lambdas[N-1] * np.cos(phases[N-1]) * (u[N-2]**2) - nu * (lambdas[N-1]**2) * u[N-1]

    return du


def make_cascade_event(lambdas, top_fraction_threshold=0.9):
    """Event that fires when the terminal shell holds >= top_fraction_threshold
    of total enstrophy -- the truncated-model analogue of the cascade reaching
    arbitrarily small scales, and (unlike a fixed absolute enstrophy value)
    reachable for any N."""
    def cascade_event(t, y, *args):
        enstrophy = np.sum((lambdas**2) * (y**2)) + 1e-300
        top_frac = (lambdas[-1]**2 * y[-1]**2) / enstrophy
        return top_fraction_threshold - top_frac
    cascade_event.terminal = True
    cascade_event.direction = -1
    return cascade_event


def run_rigorous_simulation(phases, N=22, t_max=5.0, nu=1e-5):
    lambdas = 2.0 ** np.arange(N)
    u0 = np.zeros(N)
    u0[0] = 1.0  # Initial energy injection at large scale

    event = make_cascade_event(lambdas)

    sol = solve_ivp(
        dyadic_rhs,
        [0, t_max],
        u0,
        args=(phases, lambdas, N, nu),
        method='Radau', # Implicit stiff solver to avoid numerical dissipation
        events=event,
        rtol=1e-8,
        atol=1e-11,
        dense_output=True
    )

    cascade_completed = sol.status == 1
    if sol.status < 0:
        print(f"    [-] Warning: Solver encountered convergence failure: {sol.message}")
    elif cascade_completed:
        print(f"    [+] Cascade reached the truncation scale at t* = {sol.t[-1]:.4f} s "
              f"(90% of enstrophy in the terminal shell).")
    else:
        print(f"    [ ] Did not reach the truncation scale by t_max = {sol.t[-1]:.4f} s.")

    times = sol.t
    u_t = sol.y
    enstrophies = np.sum((lambdas[:, None]**2) * (u_t**2), axis=0)

    return times, enstrophies, u_t[:, -1], lambdas, cascade_completed


def main():
    print("=" * 75)
    print(" DYADIC SIGN FRAGILITY AUDIT: 1D SHELL MODEL Observation")
    print("=" * 75)
    print("Framework: Katz-Pavlović / Desnyansky-Novikov Dyadic Euler Cascade")
    print("Integrator: Implicit Radau (Stiff ODE Solver)")
    print("Mathematical Issue: Manufactured phase-coherence theta_n = 0 identically.\n")

    N = 22
    t_max = 5.0
    # nu=0 (inviscid) isolates the phase-coherence effect being tested here:
    # with even the originally-used nu=1e-5, viscous damping (nu*lambda_n^2,
    # growing as 4^n) is enough on its own to keep EVERY case -- including the
    # fully coherent one -- from ever reaching the truncation scale within a
    # reasonable t_max, which would hide the phase-structure comparison this
    # script is actually about. Rerun with nu>0 separately if the physically
    # dissipated (as opposed to purely inviscid) cascade timescale is of
    # interest; it is a different, also-legitimate question from this one.
    nu = 0.0

    # 1. Coherent Case (OpenAI paradigm: all phases strictly aligned = 0)
    phases_coherent = np.zeros(N)

    # 2a. Complete local decoupling (theta_6 = pi/2 => cos(theta_6) = 0, which
    #     SEVERS shell 6 from the cascade entirely -- this is not a generic
    #     "disruption," it is a full local cut, and is now labeled as such.)
    phases_severed = np.zeros(N)
    phases_severed[6] = np.pi / 2.0

    # 2b. Partial local perturbation (a genuinely partial phase shift at the
    #     same shell, for contrast against the full cut above).
    phases_partial = np.zeros(N)
    phases_partial[6] = np.pi / 6.0  # cos(pi/6) = 0.866: a ~13% reduction, not a cut

    # 3. Turbulent phase jitter, wide enough to include sign flips (the
    #    previous [-pi/3, pi/3] range has cos(theta) > 0 everywhere, so no
    #    transfer ever actually changed sign despite this script's title).
    np.random.seed(42)
    phases_random = np.random.uniform(-np.pi, np.pi, size=N)
    phases_random[0] = 0.0
    n_sign_flips = int(np.sum(np.cos(phases_random[1:]) < 0))

    print("[1/4] Integrating Case A: Strictly Coherent Dyadic Cascade (theta = 0)...")
    t_coh, ens_coh, spec_coh, lambdas, done_coh = run_rigorous_simulation(phases_coherent, N, t_max, nu)

    print("[2/4] Integrating Case B1: Complete Local Decoupling (theta_6 = pi/2)...")
    t_sev, ens_sev, spec_sev, _, done_sev = run_rigorous_simulation(phases_severed, N, t_max, nu)

    print("[3/4] Integrating Case B2: Partial Local Perturbation (theta_6 = pi/6)...")
    t_par, ens_par, spec_par, _, done_par = run_rigorous_simulation(phases_partial, N, t_max, nu)

    print(f"[4/4] Integrating Case C: Turbulent Phase Jitter, [-pi,pi] ({n_sign_flips}/{N-1} "
          f"transfers have a sign flip this run)...")
    t_rnd, ens_rnd, spec_rnd, _, done_rnd = run_rigorous_simulation(phases_random, N, t_max, nu)

    max_ens_coh = np.max(ens_coh)
    max_ens_sev = np.max(ens_sev)
    max_ens_par = np.max(ens_par)
    max_ens_rnd = np.max(ens_rnd)

    def status_str(done, t_arr):
        return f"CASCADE COMPLETE (t*={t_arr[-1]:.3f})" if done else f"DID NOT COMPLETE (t_max={t_arr[-1]:.2f})"

    print("\n" + "=" * 90)
    print(f"{'Simulation Configuration':<38} | {'Max Enstrophy':<14} | {'Status':<30}")
    print("=" * 90)
    print(f"{'Coherent Cascade (theta=0)':<38} | {max_ens_coh:>12.3e} | {status_str(done_coh, t_coh):<30}")
    print(f"{'Complete Local Decoupling (n=6)':<38} | {max_ens_sev:>12.3e} | {status_str(done_sev, t_sev):<30}")
    print(f"{'Partial Local Perturbation (n=6)':<38} | {max_ens_par:>12.3e} | {status_str(done_par, t_par):<30}")
    print(f"{'Turbulent Phase Jitter [-pi,pi]':<38} | {max_ens_rnd:>12.3e} | {status_str(done_rnd, t_rnd):<30}")
    print("=" * 90)

    print("\n[EPISTEMIC VERDICT] (derived from the table above, not asserted independently of it)")
    if done_coh and not done_sev:
        print("  - A single COMPLETE local decoupling (cos(theta_n)=0 at one shell) does arrest the")
        print("    cascade within t_max, as expected: it severs the transfer chain outright.")
    if done_coh and done_par:
        speed_ratio = t_par[-1] / t_coh[-1] if done_par and done_coh else float('nan')
        print(f"  - A merely PARTIAL perturbation at the same shell (cos={np.cos(np.pi/6):.3f} instead of 0)")
        print(f"    barely slows the cascade (completes at t*={t_par[-1]:.3f} vs t*={t_coh[-1]:.3f} for the")
        print(f"    coherent case, a {speed_ratio:.2f}x change) -- i.e. the model is fragile to a full local")
        print(f"    cut, but NOT obviously fragile to a generic partial phase perturbation at one shell.")
    if done_coh and done_rnd:
        print(f"  - Even WIDE, sign-flipping phase jitter ({n_sign_flips}/{N-1} transfers reversed sign this")
        print(f"    run) still reaches cascade completion within t_max (t*={t_rnd[-1]:.3f} vs t*={t_coh[-1]:.3f}");
        print(f"    for the coherent case) -- delayed, not arrested, in this truncated model and t_max.")
    elif done_coh and not done_rnd:
        print(f"  - Wide, sign-flipping phase jitter did NOT complete the cascade within t_max="
              f"{t_max}, unlike the coherent case -- this run does support a genuine fragility claim")
        print(f"    for this specific random draw (seed=42); rerun with other seeds before generalizing.")
    print("  Read this as a demonstration that requires care in what it claims: a single full local")
    print("  cut is trivially sufficient to break any chain-structured cascade; whether GENERIC or")
    print("  distributed phase disorder is enough is a separate, and here only partially supported,")
    print("  question -- see the partial-perturbation and wide-jitter rows above.")

    # Plotting
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Subplot 1: Enstrophy growth over time
    ax1.semilogy(t_coh, ens_coh, 'r-', linewidth=2.5, label='Coherent (theta=0)')
    ax1.semilogy(t_sev, ens_sev, 'b--', linewidth=2.0, label='Complete decoupling (n=6, pi/2)')
    ax1.semilogy(t_par, ens_par, 'm:', linewidth=2.0, label='Partial perturbation (n=6, pi/6)')
    ax1.semilogy(t_rnd, ens_rnd, 'g-.', linewidth=2.0, label=f'Wide jitter [-pi,pi] ({n_sign_flips} sign flips)')
    ax1.set_xlabel('Time $t$', fontsize=12)
    ax1.set_ylabel('Enstrophy $\\Omega(t) = \\sum \\lambda_n^2 u_n^2(t)$', fontsize=12)
    ax1.set_title('Enstrophy Growth vs. Phase Structure (Radau Stiff Solver)', fontsize=13, fontweight='bold')
    ax1.grid(True, which="both", ls=":", alpha=0.6)
    ax1.legend(fontsize=9, loc='upper left')

    # Subplot 2: Ultraviolet Spectral Energy Profile at Final Time
    ax2.semilogy(np.arange(N), spec_coh**2, 'ro-', linewidth=2, label=f'Coherent ($t={t_coh[-1]:.2f}$)')
    ax2.semilogy(np.arange(N), spec_sev**2, 'bs--', linewidth=2, label=f'Decoupled ($t={t_sev[-1]:.2f}$)')
    ax2.semilogy(np.arange(N), spec_par**2, 'm^:', linewidth=2, label=f'Partial ($t={t_par[-1]:.2f}$)')
    ax2.semilogy(np.arange(N), spec_rnd**2, 'g^-.', linewidth=2, label=f'Jittered ($t={t_rnd[-1]:.2f}$)')
    ax2.set_xlabel('Dyadic Octave index $n$ (Wavenumber $\\lambda_n = 2^n$)', fontsize=12)
    ax2.set_ylabel('Modal Energy $u_n^2$', fontsize=12)
    ax2.set_title('UV Energy Distribution at $t_{final}$', fontsize=13, fontweight='bold')
    ax2.grid(True, which="both", ls=":", alpha=0.6)
    ax2.legend(fontsize=9)

    plt.tight_layout()
    output_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dyadic_sign_fragility.png')
    plt.savefig(output_png, dpi=300)
    print(f"\n[FIGURE] Saved rigorous empirical verification figure to: {output_png}")


if __name__ == '__main__':
    main()
