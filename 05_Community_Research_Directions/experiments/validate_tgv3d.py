"""
Validation of the 3D pseudo-spectral solver (research direction 1).

Nothing downstream is worth anything if the solver is wrong, so this runs the
checks that can actually fail, and reports numbers rather than verdicts.

Checks
------
V1  Taylor-Green initial invariants           E(0) = 1/8 exactly, Omega(0) = 3/8
V2  Divergence floor, and the artifact        TGV ~1e-32 (special), random ~1e-16 (real)
V3  Energy balance                            dE/dt = -epsilon along the trajectory
V4  IFRK4 vs the DualScale package's RK4      agreement in a non-stiff regime
V5  Grid convergence                          32^3 -> 48^3 -> 64^3 at fixed Re
V6  Taylor-Green transition benchmark         peak dissipation vs published values

V6 reference (Brachet et al. 1983; van Rees et al. 2011; 1st Int. Workshop on
High-Order CFD Methods): for Re = 1/nu = 1600 with U0 = L = 1 on [0,2pi)^3, the
volume-averaged dissipation rate -dE/dt peaks at t ~ 9.0 with a value ~1.25e-2.
That case needs ~256^3 for a converged DNS, so at the resolutions run here it is
reported as under-resolved and used as a *peak-time* check only -- an
under-resolved spectral run typically overpredicts the peak because energy piles
up at the cutoff instead of dissipating.

Usage:  python3 validate_tgv3d.py [--quick]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from spectral3d import HAVE_DUALSCALE, PseudoSpectralNavierStokes3D

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

TGV_RE1600_REFERENCE = {"peak_time": 9.0, "peak_dissipation": 1.25e-2, "source": "Brachet+1983; van Rees+2011"}


def v1_invariants() -> dict:
    s = PseudoSpectralNavierStokes3D(n_grid=32, nu=1e-2)
    u = s.initialize_taylor_green()
    e, om = s.energy(u), s.enstrophy(u)
    return {
        "energy": e, "energy_expected": 0.125, "energy_error": abs(e - 0.125),
        "enstrophy": om, "enstrophy_expected": 0.375, "enstrophy_error": abs(om - 0.375),
        "pass": abs(e - 0.125) < 1e-12 and abs(om - 0.375) < 1e-12,
    }


def v2_divergence_floor() -> dict:
    """
    The point of this check is the *contrast*. A previously published benchmark
    in this program reported |div u| ~ 1e-32 as 'exact machine zero', evidence of
    a superior method. It is nothing of the sort: the Taylor-Green field has a
    handful of nonzero modes with power-of-two coefficients, so k.u cancels
    exactly in binary. The same solver on a generic solenoidal field gives the
    ordinary float64 answer.
    """
    s = PseudoSpectralNavierStokes3D(n_grid=32, nu=1e-2)
    tgv = s.divergence_report(s.initialize_taylor_green())
    rnd = s.divergence_report(s.initialize_random_solenoidal(seed=1))
    return {
        "taylor_green_relative": tgv["div_l2_relative"],
        "taylor_green_absolute": tgv["div_l2_absolute"],
        "random_field_relative": rnd["div_l2_relative"],
        "random_field_absolute": rnd["div_l2_absolute"],
        "float64_epsilon": float(np.finfo(np.float64).eps),
        "interpretation": (
            "The Taylor-Green figure is an artifact of that initial condition's binary "
            "representability, not a property of the method. The random-field figure "
            "(~1e-16 relative) is the method's actual divergence floor."
        ),
    }


def v3_energy_balance(n: int = 32, nu: float = 1e-2, t_end: float = 1.0) -> dict:
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    r = s.run(s.initialize_taylor_green(), t_end=t_end, cfl=0.4, diagnostics_every=2)
    t, E, eps = r["t"], r["energy"], r["dissipation"]
    dEdt = np.gradient(E, t)
    mid = slice(2, -2)
    rel = float(np.max(np.abs(dEdt[mid] + eps[mid])) / np.max(eps[mid]))
    return {
        "max_relative_imbalance": rel,
        "energy_monotone_decreasing": bool(np.all(np.diff(E) <= 1e-14)),
        "max_div_relative": float(np.max(r["div_rel"])),
        "note": "residual is dominated by the finite-difference dE/dt, not the solver",
        "pass": rel < 5e-3,
    }


def v4_cross_check_dualscale(n: int = 32, steps: int = 40, dt: float = 2e-3) -> dict:
    if not HAVE_DUALSCALE:
        return {"skipped": "dualscale_solver not importable"}
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=1e-2)
    u0 = s.initialize_random_solenoidal(seed=3, energy=0.1)
    a, b, t = u0.copy(), u0.copy(), 0.0
    for _ in range(steps):
        a = s.ifrk4_step(a, dt)
        b = s.rk4_step_reference(t, b, dt)
        t += dt
    rel = float(np.sqrt(np.sum(np.abs(a - b) ** 2)) / np.sqrt(np.sum(np.abs(a) ** 2)))
    return {
        "relative_difference": rel,
        "steps": steps, "dt": dt,
        "note": "IFRK4 (this module) vs rk4_step from dualscale_solver.numeric.rk4_integrator",
        "pass": rel < 1e-8,
    }


def v5_grid_convergence(nu: float = 2e-2, t_end: float = 2.0, grids=(32, 48, 64)) -> dict:
    out = {}
    for n in grids:
        s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
        t0 = time.time()
        r = s.run(s.initialize_taylor_green(), t_end=t_end, cfl=0.4, diagnostics_every=4)
        out[str(n)] = {
            "final_energy": float(r["energy"][-1]),
            "final_enstrophy": float(r["enstrophy"][-1]),
            "peak_dissipation": float(np.max(r["dissipation"])),
            "wall_time_s": round(time.time() - t0, 1),
            "steps": int(r["steps"]),
        }
    keys = [str(g) for g in grids]
    diffs = [
        abs(out[keys[i + 1]]["final_energy"] - out[keys[i]]["final_energy"])
        / out[keys[i + 1]]["final_energy"]
        for i in range(len(keys) - 1)
    ]
    out["successive_relative_differences"] = diffs
    out["converging"] = bool(len(diffs) < 2 or diffs[-1] <= diffs[0])
    return out


def v6_tgv_benchmark(n: int = 64, re: float = 1600.0, t_end: float = 10.5) -> dict:
    nu = 1.0 / re
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    t0 = time.time()
    r = s.run(s.initialize_taylor_green(), t_end=t_end, cfl=0.4, diagnostics_every=4)
    eps, t = r["dissipation"], r["t"]
    i = int(np.argmax(eps))
    # Resolution adequacy: k_max * eta should exceed ~1 for a resolved DNS
    eta = s.kolmogorov_scale(r["u_hat_final"])
    kmax_eta = s.k_max_effective * eta
    return {
        "n_grid": n, "Re": re,
        "peak_dissipation": float(eps[i]),
        "peak_time": float(t[i]),
        "reference": TGV_RE1600_REFERENCE if abs(re - 1600) < 1 else None,
        "peak_time_error": (float(abs(t[i] - TGV_RE1600_REFERENCE["peak_time"]))
                            if abs(re - 1600) < 1 else None),
        "kmax_eta_final": float(kmax_eta),
        "resolved": bool(kmax_eta > 1.0),
        "max_div_relative": float(np.max(r["div_rel"])),
        "wall_time_s": round(time.time() - t0, 1),
        "caveat": (
            "At this resolution Re=1600 is under-resolved (a converged DNS needs ~256^3); "
            "treat the peak TIME as the meaningful comparison and expect the peak "
            "MAGNITUDE to be overpredicted as energy accumulates near the cutoff."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip the expensive V5/V6 runs")
    args = ap.parse_args()

    results = {
        "V1_taylor_green_invariants": v1_invariants(),
        "V2_divergence_floor": v2_divergence_floor(),
        "V3_energy_balance": v3_energy_balance(),
        "V4_cross_check_dualscale": v4_cross_check_dualscale(),
    }
    if not args.quick:
        results["V5_grid_convergence"] = v5_grid_convergence()
        results["V6_tgv_re1600"] = v6_tgv_benchmark()

    path = OUT / "validation_3d.json"
    path.write_text(json.dumps(results, indent=2))

    print("=" * 72)
    print(" 3D PSEUDO-SPECTRAL SOLVER VALIDATION")
    print("=" * 72)
    v1 = results["V1_taylor_green_invariants"]
    print(f"V1 invariants      E={v1['energy']:.10f} (exp 0.125)  Om={v1['enstrophy']:.10f} (exp 0.375)  -> {'PASS' if v1['pass'] else 'FAIL'}")
    v2 = results["V2_divergence_floor"]
    print(f"V2 divergence      Taylor-Green {v2['taylor_green_relative']:.2e} (special/binary-exact)")
    print(f"                   random field {v2['random_field_relative']:.2e} <- the real floor, ~float64 eps {v2['float64_epsilon']:.1e}")
    v3 = results["V3_energy_balance"]
    print(f"V3 energy balance  |dE/dt+eps|/eps = {v3['max_relative_imbalance']:.2e}, monotone={v3['energy_monotone_decreasing']} -> {'PASS' if v3['pass'] else 'FAIL'}")
    v4 = results["V4_cross_check_dualscale"]
    if "skipped" in v4:
        print(f"V4 cross-check     SKIPPED ({v4['skipped']})")
    else:
        print(f"V4 vs DualScale    relative difference {v4['relative_difference']:.2e} -> {'PASS' if v4['pass'] else 'FAIL'}")
    if not args.quick:
        v5 = results["V5_grid_convergence"]
        print(f"V5 grid convergence successive rel. diffs {['%.2e' % d for d in v5['successive_relative_differences']]} -> {'converging' if v5['converging'] else 'CHECK'}")
        for g in ("32", "48", "64"):
            print(f"                   {g}^3: E_final={v5[g]['final_energy']:.6f}  {v5[g]['wall_time_s']}s")
        v6 = results["V6_tgv_re1600"]
        print(f"V6 TGV Re=1600     peak eps={v6['peak_dissipation']:.4e} at t={v6['peak_time']:.2f}")
        print(f"                   reference: {TGV_RE1600_REFERENCE['peak_dissipation']:.4e} at t={TGV_RE1600_REFERENCE['peak_time']}")
        print(f"                   peak-time error {v6['peak_time_error']:.2f}; kmax*eta={v6['kmax_eta_final']:.2f} resolved={v6['resolved']}")
    print(f"\nwritten to {path}")


if __name__ == "__main__":
    main()
