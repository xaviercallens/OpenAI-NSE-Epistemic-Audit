"""
Research direction 2: the first actual test of the cutoff law.

The claim under test
--------------------
The flagship paper states, explicitly as an untested hypothesis: if a
regularization arrests the collapse when the core radius reaches sqrt(alpha'),
then because the collapsing core of the OpenAI construction keeps a radial
Reynolds number of order one,

        l_r ~ sqrt(nu t),      u ~ sqrt(nu / t),

the arrest happens at

        t_c   ~ alpha'/nu                            (P1)
        u_max ~ nu / sqrt(alpha')                    (P2)
        w_max ~ u_max / l_arrest ~ nu / alpha'       (P3)
        l_arrest ~ sqrt(alpha')                      (P4)

and setting sqrt(alpha') = l_* = nu/c_s gives u_max ~ c_s, consistent with
Proposition 5.1.

The premise matters as much as the prediction
---------------------------------------------
Every one of P1-P4 follows from the *diffusive core scaling*, which is a
property of a Re ~ 1 collapsing core -- not of turbulence in general. In a
decaying flow started from O(1) data, the velocity does not grow, and the law
has no purchase. So this script tests the premise first and reports it
separately:

        PREMISE CHECK:  Re_core = u_max * l_arrest / nu  ~  O(1)?

If Re_core is not O(1), the flow is not in the regime the law describes, and a
failure of P1-P4 is *not* evidence against the law -- it is evidence that this
initial condition does not realize the law's hypotheses. Reporting that
distinction honestly is the whole point; a previous benchmark in this program
swept alpha' over five decades, saw max enstrophy move by 0.02%, and reported an
enstrophy ceiling as if it had been demonstrated, when in fact the barrier was
never engaged at all.

Controls enforced for every run
-------------------------------
  C1  the barrier must be resolved:        1 < k_alpha < (2/3)(N/2)
  C2  the barrier must bite before viscosity does:   k_alpha < k_eta = 1/eta
      (otherwise ordinary dissipation sets the smallest scale and alpha' is inert)
  C3  the run must actually be arrested, not merely decaying: the dissipation
      spectrum must peak at k_alpha, not at the box scale

Runs that fail C1-C3 are recorded and excluded from the fit, with the reason.

Usage:
    python3 sweep_cutoff_law.py --n 64 --ic tubes
    python3 sweep_cutoff_law.py --n 96 --ic tgv --points 8
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from spectral3d import PseudoSpectralNavierStokes3D

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

PREDICTIONS = {
    "t_c": {"exponent": 1.0, "law": "t_c ~ alpha'/nu"},
    "u_max": {"exponent": -0.5, "law": "u_max ~ nu/sqrt(alpha')"},
    "omega_max": {"exponent": -1.0, "law": "omega_max ~ nu/alpha'"},
    "l_arrest": {"exponent": 0.5, "law": "l_arrest ~ sqrt(alpha')"},
}


def dissipation_spectrum_peak(solver, u_hat) -> tuple[float, float]:
    """Return (k_peak, l_arrest) where the dissipation spectrum D(k)=2|L(k)|E(k) peaks."""
    k, e_k = solver.energy_spectrum(u_hat)
    kbin = np.rint(solver.k_mag).astype(int)
    nk = solver.n // 2
    weight = 2.0 * np.abs(solver.diss_symbol) * np.sum(np.abs(u_hat) ** 2, axis=0) / (solver.n ** 6) / 2.0
    d_k = np.bincount(kbin.ravel(), weights=weight.ravel(), minlength=nk + 1)[: nk + 1]
    if d_k[1:].sum() <= 0:
        return float("nan"), float("nan")
    kp = int(np.argmax(d_k[1:]) + 1)
    return float(kp), float(2.0 * np.pi / kp)


def run_one(n: int, nu: float, alpha_prime: float, ic: str, t_end: float,
            dissipation: str = "barrier") -> dict:
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, alpha_prime=alpha_prime,
                                     dissipation=dissipation)
    if ic == "tgv":
        u0 = s.initialize_taylor_green()
    elif ic == "tubes":
        u0 = s.initialize_colliding_vortex_tubes()
    elif ic == "random":
        u0 = s.initialize_random_solenoidal(seed=7)
    else:
        raise ValueError(ic)

    t0 = time.time()
    r = s.run(u0, t_end=t_end, cfl=0.4, diagnostics_every=4)
    wall = time.time() - t0

    w = r["omega_max"]
    i_peak = int(np.argmax(w))
    u_hat_peak = r["u_hat_final"]  # spectrum at the end; peak-time state not retained
    k_peak, l_arrest = dissipation_spectrum_peak(s, u_hat_peak)

    eta = s.kolmogorov_scale(r["u_hat_final"])
    k_eta = 1.0 / eta if np.isfinite(eta) and eta > 0 else np.inf
    k_alpha = s.barrier_wavenumber

    u_at_peak = float(r["u_max"][i_peak])
    re_core = u_at_peak * l_arrest / nu if np.isfinite(l_arrest) else float("nan")

    # controls
    c1 = bool(s.barrier_is_resolved())
    c2 = bool(k_alpha < k_eta)
    c3 = bool(np.isfinite(k_peak) and abs(k_peak - k_alpha) / k_alpha < 0.75)
    return {
        "alpha_prime": alpha_prime,
        "k_alpha": k_alpha,
        "omega_max": float(w[i_peak]),
        "u_max": u_at_peak,
        "t_peak": float(r["t"][i_peak]),
        "l_arrest": l_arrest,
        "k_dissipation_peak": k_peak,
        "k_eta": float(k_eta),
        "Re_core": float(re_core),
        "final_energy": float(r["energy"][-1]),
        "peak_enstrophy": float(np.max(r["enstrophy"])),
        "max_div_relative": float(np.max(r["div_rel"])),
        "wall_time_s": round(wall, 1),
        "C1_barrier_resolved": c1,
        "C2_barrier_before_viscosity": c2,
        "C3_dissipation_peaks_at_barrier": c3,
        "usable": c1 and c2 and c3,
        "exclusion_reason": (
            None if (c1 and c2 and c3)
            else ("barrier outside resolved band" if not c1
                  else "viscosity bites first" if not c2
                  else "dissipation does not peak at the barrier (flow not arrested there)")
        ),
    }


def fit_power_law(x: np.ndarray, y: np.ndarray) -> dict:
    """Least-squares fit of log y = a log x + b, with a bootstrap CI on a."""
    ok = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    x, y = x[ok], y[ok]
    if len(x) < 3:
        return {"exponent": float("nan"), "n_points": int(len(x)),
                "insufficient_data": True}
    lx, ly = np.log(x), np.log(y)
    a, b = np.polyfit(lx, ly, 1)
    resid = ly - (a * lx + b)
    ss_tot = np.sum((ly - ly.mean()) ** 2)
    r2 = 1.0 - np.sum(resid ** 2) / ss_tot if ss_tot > 0 else float("nan")
    rng = np.random.default_rng(0)
    boots = []
    for _ in range(2000):
        idx = rng.integers(0, len(lx), len(lx))
        if len(np.unique(idx)) < 2:
            continue
        boots.append(np.polyfit(lx[idx], ly[idx], 1)[0])
    lo, hi = (np.percentile(boots, [2.5, 97.5]) if boots else (float("nan"), float("nan")))
    return {"exponent": float(a), "r_squared": float(r2), "n_points": int(len(x)),
            "ci95": [float(lo), float(hi)],
            "decades_spanned": float(np.log10(x.max() / x.min()))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=64)
    ap.add_argument("--nu", type=float, default=2e-3)
    ap.add_argument("--ic", default="tubes", choices=["tubes", "tgv", "random"])
    ap.add_argument("--points", type=int, default=7)
    ap.add_argument("--t-end", type=float, default=4.0)
    ap.add_argument("--dissipation", default="barrier", choices=["barrier", "bihyper"])
    ap.add_argument("--k-lo", type=float, default=None,
                    help="lowest barrier wavenumber k_alpha (default 3)")
    ap.add_argument("--k-hi", type=float, default=None,
                    help="highest barrier wavenumber (default 0.8*k_max)")
    args = ap.parse_args()

    # Choose alpha' so k_alpha spans the requested band.
    #
    # The binding constraint, derived in the accompanying write-up: the barrier
    # caps vorticity at omega_cap = nu/alpha' = nu k_alpha^2, and k_alpha must
    # stay inside the resolved band, so the largest achievable cap is
    # nu*k_max^2. For the barrier to arrest a *growing* vorticity rather than
    # merely damp the initial field, one needs omega_0 < nu k_max^2, i.e.
    #     n > 3*sqrt(omega_0/nu) = 3*sqrt(omega_0*Re).
    # For the Taylor-Green vortex (omega_0 = 2) that is n > 85 at Re = 400 and
    # n > 170 at Re = 1600 -- which is why the earlier 64^3 attempts in this
    # program saw no effect whatsoever from alpha'.
    k_max_eff = (2.0 / 3.0) * (args.n / 2.0)
    k_lo = args.k_lo if args.k_lo is not None else 3.0
    k_hi = args.k_hi if args.k_hi is not None else 0.8 * k_max_eff
    alphas = 1.0 / np.logspace(np.log10(k_lo), np.log10(k_hi), args.points) ** 2
    print(f" implied vorticity caps nu/alpha' = nu*k_alpha^2: "
          f"{args.nu*k_lo**2:.2f} .. {args.nu*k_hi**2:.2f}"
          f"   (max achievable at this grid: {args.nu*k_max_eff**2:.2f})")

    print("=" * 78)
    print(" CUTOFF-LAW SWEEP -- first direct test of the paper's Q1")
    print("=" * 78)
    print(f" grid {args.n}^3   nu={args.nu:g}   IC={args.ic}   operator={args.dissipation}")
    print(f" alpha' from {alphas.min():.3e} to {alphas.max():.3e}"
          f"  ({np.log10(alphas.max()/alphas.min()):.2f} decades)")
    print(f" k_alpha from {1/np.sqrt(alphas.max()):.1f} to {1/np.sqrt(alphas.min()):.1f}"
          f"   (resolved band: 1 .. {k_max_eff:.1f})\n")

    runs = []
    for ap_val in sorted(alphas):
        r = run_one(args.n, args.nu, float(ap_val), args.ic, args.t_end, args.dissipation)
        runs.append(r)
        flag = "ok " if r["usable"] else "EXCL"
        print(f" [{flag}] alpha'={ap_val:.3e} k_a={r['k_alpha']:5.1f} "
              f"w_max={r['omega_max']:8.3f} u_max={r['u_max']:6.3f} "
              f"t_peak={r['t_peak']:5.2f} Re_core={r['Re_core']:7.2f} "
              f"({r['wall_time_s']}s)"
              + (f"  <- {r['exclusion_reason']}" if not r["usable"] else ""))

    usable = [r for r in runs if r["usable"]]
    a = np.array([r["alpha_prime"] for r in usable])
    fits = {}
    if len(usable) >= 3:
        for key in ("t_peak", "u_max", "omega_max", "l_arrest"):
            y = np.array([r[key] for r in usable])
            pred_key = {"t_peak": "t_c"}.get(key, key)
            f = fit_power_law(a, y)
            f["predicted_exponent"] = PREDICTIONS[pred_key]["exponent"]
            f["law"] = PREDICTIONS[pred_key]["law"]
            if np.isfinite(f.get("exponent", np.nan)) and "ci95" in f:
                f["consistent_with_prediction"] = bool(
                    f["ci95"][0] <= PREDICTIONS[pred_key]["exponent"] <= f["ci95"][1]
                )
            fits[key] = f

    re_core_vals = np.array([r["Re_core"] for r in usable]) if usable else np.array([])
    premise = {
        "Re_core_values": re_core_vals.tolist(),
        "Re_core_median": float(np.median(re_core_vals)) if len(re_core_vals) else None,
        "premise_holds": (bool(0.1 < np.median(re_core_vals) < 10.0)
                          if len(re_core_vals) else None),
        "note": ("The cutoff law is a statement about a Re~1 diffusive core. If Re_core "
                 "is far from O(1), this flow does not realize the law's hypotheses and "
                 "the exponent fits below do not test it."),
    }

    out = {
        "config": vars(args),
        "runs": runs,
        "n_usable": len(usable),
        "premise_check": premise,
        "power_law_fits": fits,
        "predictions": PREDICTIONS,
    }
    path = OUT / f"cutoff_law_{args.ic}_{args.n}.json"
    path.write_text(json.dumps(out, indent=2))

    print("\n" + "-" * 78)
    print(f" PREMISE CHECK   Re_core median = {premise['Re_core_median']}"
          f"   -> premise {'HOLDS' if premise['premise_holds'] else 'DOES NOT HOLD'}")
    if not premise["premise_holds"]:
        print("   The exponent fits below therefore do NOT constitute a test of the law.")
    print("-" * 78)
    if fits:
        print(f" {'quantity':<12}{'fitted':>9}{'predicted':>11}{'R^2':>8}  {'95% CI':<20} consistent")
        for k, f in fits.items():
            if "exponent" not in f or not np.isfinite(f["exponent"]):
                continue
            ci = f"[{f['ci95'][0]:+.2f}, {f['ci95'][1]:+.2f}]"
            print(f" {k:<12}{f['exponent']:>+9.3f}{f['predicted_exponent']:>+11.2f}"
                  f"{f['r_squared']:>8.3f}  {ci:<20} {f.get('consistent_with_prediction')}")
    else:
        print(" Not enough usable runs to fit. See exclusion reasons above.")
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
