"""
Research direction 2, wide-range companion: the cutoff law in a dyadic shell model.

Why this exists
---------------
The 3D DNS test (sweep_cutoff_law.py) is limited by a hard resolution constraint.
The barrier caps vorticity at omega_cap = nu/alpha' = nu*k_alpha^2, and k_alpha
must lie inside the resolved band, so the largest achievable cap is nu*k_max^2.
Requiring the barrier to arrest *growing* vorticity rather than merely damp the
initial field gives

        n > 3*sqrt(omega_0 * Re),

i.e. n > 85 at Re = 400 and n > 170 at Re = 1600 for the Taylor-Green vortex.
Even at n = 96 the usable band in alpha' is well under one decade -- too thin to
fit an exponent with confidence.

A dyadic shell model has no such constraint: with 30 shells and lambda = 2 the
wavenumber range spans about nine decades, so the barrier can be placed deep
inside an inertial range and swept over many decades of alpha'.

What this does and does not show
--------------------------------
A shell model is NOT the Navier-Stokes equation. This project's own errata
record that point ("A shell model is not the Euler equation"), and it applies
here with full force: the shell model has no geometry, no vortex stretching in
the real sense, no incompressibility constraint, and a single scalar per octave.

What it *can* test is the balance argument the cutoff law rests on: that
vorticity grows until the nonlinear transfer rate is matched by the barrier's
damping rate at the barrier scale, giving

        omega_max ~ nu * k_alpha^2 = nu/alpha'          (exponent -1 in alpha')
        u(k_alpha) ~ nu * k_alpha  = nu/sqrt(alpha')    (exponent -1/2 in alpha')

If those exponents fail *here*, the balance argument itself is wrong and the DNS
result would not rescue it. If they hold here, the law's mechanism is consistent
in a system with a genuine cascade -- which is suggestive, not decisive.

Uses DyadicShellSolver from the DualScale solver package (its dissipation
operator is already nu*k^2*max(1, alpha'*k^2), the barrier form).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from spectral3d import HAVE_DUALSCALE

if not HAVE_DUALSCALE:  # pragma: no cover
    raise SystemExit("dualscale_solver not importable; set PYTHONPATH to its src/ directory")

from dualscale_solver.numeric.dyadic_cascade import DyadicShellSolver  # noqa: E402

from sweep_cutoff_law import fit_power_law  # noqa: E402

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)


def run_shell(alpha_prime: float | None, nu: float, n_shells: int, t_end: float,
              dt: float, forcing_amp: float) -> dict:
    s = DyadicShellSolver(
        n_shells=n_shells, k0=1.0, inter_shell_ratio=2.0, nu=nu,
        alpha_prime=alpha_prime, forcing_shell=0, forcing_amp=forcing_amp,
    )
    u0 = np.zeros(n_shells)
    u0[0] = 1e-3
    res = s.solve((0.0, t_end), u0, dt)

    traj = np.asarray(res["trajectory"]) if "trajectory" in res else None
    u_final = traj[-1] if traj is not None else np.asarray(res["u_final"])
    # Average over the last 20% of the record to smooth cascade fluctuations
    if traj is not None and len(traj) > 10:
        tail = traj[int(0.8 * len(traj)):]
        u_rep = np.sqrt(np.mean(tail**2, axis=0))
    else:
        u_rep = np.abs(u_final)

    k = s.k
    shell_vorticity = k * u_rep          # analogue of |omega| at each scale
    omega_max = float(np.max(shell_vorticity))
    n_peak = int(np.argmax(shell_vorticity))

    k_alpha = (1.0 / np.sqrt(alpha_prime)) if alpha_prime else np.inf
    # velocity at the barrier shell (nearest shell at or below k_alpha)
    idx = int(np.searchsorted(k, k_alpha, side="right") - 1)
    idx = max(0, min(idx, n_shells - 1))
    u_at_barrier = float(u_rep[idx])

    # viscous (Kolmogorov) shell: where nu*k^2 first exceeds the local turnover k*u
    turnover = k * u_rep
    visc = nu * k**2
    above = np.nonzero(visc > np.maximum(turnover, 1e-300))[0]
    k_eta = float(k[above[0]]) if len(above) else float(k[-1])

    return {
        "alpha_prime": alpha_prime,
        "k_alpha": float(k_alpha),
        "k_eta": k_eta,
        "omega_max": omega_max,
        "k_at_omega_max": float(k[n_peak]),
        "u_at_barrier": u_at_barrier,
        "energy": float(0.5 * np.sum(u_rep**2)),
        "barrier_inside_range": bool(alpha_prime and k[0] < k_alpha < k[-1]),
        "barrier_before_viscosity": bool(alpha_prime and k_alpha < k_eta),
        "finite": bool(np.all(np.isfinite(u_rep))),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-shells", type=int, default=30)
    ap.add_argument("--nu", type=float, default=1e-10)
    ap.add_argument("--points", type=int, default=10)
    ap.add_argument("--t-end", type=float, default=60.0)
    ap.add_argument("--dt", type=float, default=1e-3)
    ap.add_argument("--forcing", type=float, default=1.0)
    ap.add_argument("--shell-lo", type=int, default=6, help="lowest barrier shell index")
    ap.add_argument("--shell-hi", type=int, default=20, help="highest barrier shell index")
    args = ap.parse_args()

    k = 2.0 ** np.arange(args.n_shells)
    shells = np.unique(np.linspace(args.shell_lo, args.shell_hi, args.points).astype(int))
    alphas = 1.0 / (k[shells] ** 2)

    print("=" * 78)
    print(" CUTOFF LAW IN A DYADIC SHELL MODEL (wide-range companion to the DNS)")
    print("=" * 78)
    print(f" shells={args.n_shells} (k up to {k[-1]:.2e})  nu={args.nu:g}  forcing={args.forcing}")
    print(f" alpha' from {alphas.min():.3e} to {alphas.max():.3e}"
          f"  ({np.log10(alphas.max()/alphas.min()):.1f} decades)")
    print(" NOTE: a shell model is not Navier-Stokes; this tests the balance argument only.\n")

    runs = [run_shell(None, args.nu, args.n_shells, args.t_end, args.dt, args.forcing)]
    print(f" [ref ] no barrier          omega_max={runs[0]['omega_max']:.4e}"
          f"  k(omega_max)={runs[0]['k_at_omega_max']:.2e}")

    for a in sorted(alphas)[::-1]:
        r = run_shell(float(a), args.nu, args.n_shells, args.t_end, args.dt, args.forcing)
        runs.append(r)
        ok = r["barrier_inside_range"] and r["barrier_before_viscosity"] and r["finite"]
        print(f" [{'ok ' if ok else 'EXCL'}] alpha'={a:.3e} k_a={r['k_alpha']:9.2e}"
              f"  omega_max={r['omega_max']:.4e}  u(k_a)={r['u_at_barrier']:.4e}"
              f"  nu/alpha'={args.nu/a:.4e}")

    usable = [r for r in runs[1:]
              if r["barrier_inside_range"] and r["barrier_before_viscosity"] and r["finite"]]
    fits = {}
    if len(usable) >= 3:
        a_arr = np.array([r["alpha_prime"] for r in usable])
        for key, pred, law in (
            ("omega_max", -1.0, "omega_max ~ nu/alpha'"),
            ("u_at_barrier", -0.5, "u(k_alpha) ~ nu/sqrt(alpha')"),
        ):
            y = np.array([r[key] for r in usable])
            f = fit_power_law(a_arr, y)
            f["predicted_exponent"] = pred
            f["law"] = law
            if np.isfinite(f.get("exponent", np.nan)) and "ci95" in f:
                f["consistent_with_prediction"] = bool(f["ci95"][0] <= pred <= f["ci95"][1])
            fits[key] = f

    out = {"config": vars(args), "runs": runs, "n_usable": len(usable),
           "power_law_fits": fits,
           "caveat": "Shell model, not Navier-Stokes. Tests the balance argument only."}
    path = OUT / "cutoff_law_shell.json"
    path.write_text(json.dumps(out, indent=2))

    print("\n" + "-" * 78)
    if fits:
        print(f" {'quantity':<16}{'fitted':>9}{'predicted':>11}{'R^2':>8}  {'95% CI':<20} decades consistent")
        for kk, f in fits.items():
            if not np.isfinite(f.get("exponent", np.nan)):
                continue
            ci = f"[{f['ci95'][0]:+.2f}, {f['ci95'][1]:+.2f}]"
            print(f" {kk:<16}{f['exponent']:>+9.3f}{f['predicted_exponent']:>+11.2f}"
                  f"{f['r_squared']:>8.3f}  {ci:<20} {f['decades_spanned']:>5.1f}"
                  f"   {f.get('consistent_with_prediction')}")
    else:
        print(" Not enough usable runs to fit.")
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
