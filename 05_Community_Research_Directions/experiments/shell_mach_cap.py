"""
Lock C, cheapest possible form: a Mach cap in the dyadic shell model.

DUAL_SCALE_LOCK_PROGRAMME.md, week item 2. This is a PHENOMENOLOGICAL PROXY,
not compressible fluid dynamics: the only physics encoded is "a shell cannot
carry velocity faster than the sound speed". The model has no pressure, no
density, no acoustics -- the cap is a saturation applied to the rate of change
of each shell velocity.

Two experiments, and the second is the point.

  1. Forced cascade. In a cascade u_n decreases with k (Kolmogorov ~k^{-1/3}),
     so the Mach constraint should bite at the LARGEST scale first. If so, the
     Mach lock is a large-scale constraint in a cascade, and only becomes a
     small-scale one on a collapse.
  2. Imposed collapse. Along the paper's Re=1 diffusive core, u = sqrt(nu/t),
     l = sqrt(nu t), the same cap engages at u = c_s, i.e. at t* = nu/c_s^2 and
     l* = nu/c_s -- Proposition 5.1's scale. That is arithmetic, not simulation,
     and it is included so the contrast with experiment 1 is explicit: one cap,
     two regimes, opposite ends of the spectrum.

Uses DyadicShellSolver from the DualScale solver package (its integrating-factor
RK4 handles the stiff viscous term; only the nonlinear RHS is overridden here).
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

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

FLUIDS = {
    "water": {"nu": 1.0e-6, "c_s": 1500.0},
    "air": {"nu": 1.56e-5, "c_s": 343.0},
}


def saturation(u: np.ndarray, c_s: float) -> np.ndarray:
    """
    s(u) = max(0, 1 - (u/c_s)^2).

    Chosen over 1/(1+(u/c_s)^2) because the latter never reaches zero, so a
    shell could still creep past c_s under sustained forcing; a *cap* should
    stop it there. The quadratic form is smooth at u=0 (no spurious linear
    damping of small velocities) and reduces to exactly 1 as c_s -> inf.
    """
    return np.maximum(0.0, 1.0 - (u / c_s) ** 2)


class MachCappedShellSolver(DyadicShellSolver):
    """
    Dyadic shell model in which every non-viscous rate of change of shell n
    (nonlinear transfer AND forcing) is multiplied by s(u_n).

    The cap is applied to the whole non-viscous RHS rather than only to the
    inflow term: if the outflow term were left uncapped, a forced shell held
    near c_s would keep draining into the next shell while its own growth was
    frozen, which is a statement about energy routing, not about a speed limit.
    Viscous damping nu k^2 is untouched (it is linear and handled exactly by
    the base class's integrating factor).
    """

    def __init__(self, *args, c_s: float = np.inf, **kwargs):
        super().__init__(*args, **kwargs)
        self.c_s = float(c_s)

    def non_linear_rhs(self, t: float, u: np.ndarray) -> np.ndarray:
        return super().non_linear_rhs(t, u) * saturation(u, self.c_s)


# --------------------------------------------------------------------------
# Experiment 1: forced cascade
# --------------------------------------------------------------------------

def run_cascade(c_s: float, nu: float, n_shells: int, t_end: float, dt: float,
                forcing_amp: float) -> dict:
    s = MachCappedShellSolver(
        n_shells=n_shells, k0=1.0, inter_shell_ratio=2.0, nu=nu,
        alpha_prime=None, forcing_shell=0, forcing_amp=forcing_amp, c_s=c_s,
    )
    u0 = np.zeros(n_shells)
    u0[0] = 1e-3
    res = s.solve((0.0, t_end), u0, dt)
    traj = np.asarray(res["trajectory"])
    tail = traj[int(0.8 * len(traj)):]
    u_rms = np.sqrt(np.mean(tail**2, axis=0))
    u_abs_max = np.max(np.abs(traj), axis=0)
    mach = u_rms / c_s if np.isfinite(c_s) else np.zeros_like(u_rms)
    sat = saturation(u_rms, c_s)
    engaged = np.nonzero(sat < 0.5)[0]           # shells with u_rms > 0.707 c_s
    return {
        "c_s": float(c_s),
        "u_rms_by_shell": u_rms.tolist(),
        "u_absmax_by_shell": u_abs_max.tolist(),
        "mach_by_shell": mach.tolist(),
        "saturation_by_shell": sat.tolist(),
        "max_mach_shell": int(np.argmax(mach)) if np.isfinite(c_s) else None,
        "max_mach": float(np.max(mach)),
        "engaged_shells": engaged.tolist(),
        "first_engaged_shell": int(engaged[0]) if len(engaged) else None,
        "finite": bool(np.all(np.isfinite(traj))),
        "energy_final": float(res["energy"][-1]),
    }


# --------------------------------------------------------------------------
# Experiment 2: the cap along an imposed Re=1 collapse (arithmetic)
# --------------------------------------------------------------------------

def collapse_crossings(nu: float, c_s: float, mach_levels=(1.0, 0.3)) -> dict:
    """
    u(t) = sqrt(nu/t), l(t) = sqrt(nu t). u = Ma*c_s at t = nu/(Ma c_s)^2,
    l = nu/(Ma c_s). At Ma = 1 these are t* and l* of Proposition 5.1.
    """
    out = {"nu": nu, "c_s": c_s, "l_star_paper": nu / c_s, "t_star_paper": nu / c_s**2}
    for ma in mach_levels:
        t = nu / (ma * c_s) ** 2
        u = np.sqrt(nu / t)
        l = np.sqrt(nu * t)
        out[f"Ma_{ma:g}"] = {"t_s": float(t), "l_m": float(l), "u_m_per_s": float(u),
                             "mach_check": float(u / c_s), "saturation": float(saturation(np.array(u), c_s))}
    out["l_at_Ma1_over_l_star"] = out["Ma_1"]["l_m"] / out["l_star_paper"]
    out["t_at_Ma1_over_t_star"] = out["Ma_1"]["t_s"] / out["t_star_paper"]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-shells", type=int, default=22)
    ap.add_argument("--nu", type=float, default=1e-6)
    ap.add_argument("--t-end", type=float, default=30.0)
    ap.add_argument("--dt", type=float, default=5e-4)
    ap.add_argument("--forcing", type=float, default=1.0)
    ap.add_argument("--c-s", type=float, nargs="+",
                    default=[0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 1e4])
    args = ap.parse_args()

    print("=" * 78)
    print(" MACH CAP IN THE DYADIC SHELL MODEL (Lock C, phenomenological proxy)")
    print("=" * 78)

    ref = run_cascade(np.inf, args.nu, args.n_shells, args.t_end, args.dt, args.forcing)
    u_ref = np.array(ref["u_rms_by_shell"])
    k = 2.0 ** np.arange(args.n_shells)
    # inertial-range slope of the uncapped cascade, shells 2..10
    sl = slice(2, 11)
    slope = float(np.polyfit(np.log(k[sl]), np.log(np.maximum(u_ref[sl], 1e-300)), 1)[0])
    print(f"\n[1] Forced cascade: uncapped u_rms(shell 0) = {u_ref[0]:.4f}, "
          f"u_rms(shell 5) = {u_ref[5]:.4f}; u ~ k^{slope:+.3f} over shells 2-10 "
          f"(Kolmogorov -1/3)")
    print(f"     largest-scale shell carries the largest velocity: "
          f"{bool(np.argmax(u_ref) == 0)}\n")

    print(f" {'c_s':>8} {'max Ma':>8} {'@shell':>7} {'engaged shells (u>0.707c_s)':>28} "
          f"{'u0 capped/uncapped':>19}")
    runs = []
    for cs in args.c_s:
        r = run_cascade(cs, args.nu, args.n_shells, args.t_end, args.dt, args.forcing)
        runs.append(r)
        eng = r["engaged_shells"]
        eng_s = (f"{eng[0]}..{eng[-1]}" if len(eng) > 1 else (str(eng[0]) if eng else "none"))
        print(f" {cs:>8.3g} {r['max_mach']:>8.3f} {r['max_mach_shell']:>7} {eng_s:>28} "
              f"{r['u_rms_by_shell'][0] / u_ref[0]:>19.3f}")

    first_engaged = [r["first_engaged_shell"] for r in runs if r["first_engaged_shell"] is not None]
    max_mach_shells = [r["max_mach_shell"] for r in runs]
    cascade_verdict = {
        "max_mach_shell_is_zero_for_all_runs": bool(all(m == 0 for m in max_mach_shells)),
        "first_engaged_shell_values": first_engaged,
        "cap_engages_at_largest_scale": bool(first_engaged and all(f == 0 for f in first_engaged)),
        "uncapped_inertial_slope": slope,
    }
    print(f"\n     Max-Mach shell is shell 0 in every run: "
          f"{cascade_verdict['max_mach_shell_is_zero_for_all_runs']}")
    print(f"     Where the cap engages, it engages at shell 0 first: "
          f"{cascade_verdict['cap_engages_at_largest_scale']}")

    print("\n[2] Same cap along an imposed Re=1 collapse u=sqrt(nu/t), l=sqrt(nu t):")
    collapse = {}
    print(f" {'fluid':>6} {'l(Ma=1)':>10} {'l* paper':>10} {'t(Ma=1)':>10} {'t* paper':>10} "
          f"{'l(Ma=0.3)':>10} {'t(Ma=0.3)':>10}")
    for name, f in FLUIDS.items():
        c = collapse_crossings(f["nu"], f["c_s"])
        collapse[name] = c
        print(f" {name:>6} {c['Ma_1']['l_m']:>10.3e} {c['l_star_paper']:>10.3e} "
              f"{c['Ma_1']['t_s']:>10.3e} {c['t_star_paper']:>10.3e} "
              f"{c['Ma_0.3']['l_m']:>10.3e} {c['Ma_0.3']['t_s']:>10.3e}")
    repro = all(abs(c["l_at_Ma1_over_l_star"] - 1) < 1e-9 and abs(c["t_at_Ma1_over_t_star"] - 1) < 1e-9
                for c in collapse.values())
    print(f"     Ma=1 crossing reproduces l* and t* of Proposition 5.1: {repro}")

    contrast = {
        "cascade_cap_at_largest_scale": cascade_verdict["cap_engages_at_largest_scale"],
        "collapse_cap_at_smallest_scale_l_star": repro,
        "same_cap_opposite_ends": bool(cascade_verdict["cap_engages_at_largest_scale"] and repro),
    }
    print(f"\n     One cap, two regimes: large-scale in a cascade, l* on a collapse -> "
          f"{contrast['same_cap_opposite_ends']}")

    out = {
        "config": vars(args) | {"c_s": list(args.c_s)},
        "reference_uncapped": ref,
        "cascade_runs": runs,
        "cascade_verdict": cascade_verdict,
        "collapse": collapse,
        "contrast": contrast,
        "caveat": ("Phenomenological proxy: a saturation on shell velocity, not compressible "
                   "dynamics. No pressure, density or acoustics are modelled."),
    }
    path = OUT / "shell_mach_cap.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
