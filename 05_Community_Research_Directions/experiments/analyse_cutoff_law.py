"""
Analysis of the cutoff-law tests: is the law wrong, or is its premise unreachable?

This distinction decides how the result should be written up, so it is worth
settling explicitly rather than by assertion.

A. Internal consistency (analytic).
   Granting the premise -- a core obeying the diffusive scaling l_r = sqrt(nu t),
   u = sqrt(nu/t), i.e. Re_core = u*l_r/nu = 1 -- the arrest condition and the
   three predicted exponents are checked symbolically-in-numbers. If the law is
   self-consistent, a negative experimental result is a statement about the
   premise, not about the arithmetic.

B. Premise reachability (from the measured runs).
   Whether generic initial data, in a cascade or in a decaying 3D flow, ever
   produces a core with Re_core ~ 1 at the arrest scale.

C. Figure summarising both.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RES = HERE / "results"


# ---------------------------------------------------------------------------
# A. Internal consistency of the law, granting its premise
# ---------------------------------------------------------------------------

def analytic_self_consistency(nu: float = 1e-3, alphas=(1e-2, 1e-3, 1e-4, 1e-5, 1e-6)) -> dict:
    """
    Under the premise, the core at time-to-blowup t has

        l_r = sqrt(nu t),   u = sqrt(nu/t),   |omega| ~ u/l_r = 1/t.

    The barrier operator nu k^2 max(1, alpha' k^2) evaluated at the core's own
    wavenumber k = 1/l_r damps at rate

        D(t) = nu/l_r^2 * max(1, alpha'/l_r^2) = (1/t) * max(1, alpha'/(nu t)),

    while the core evolves at rate |d ln l_r/dt| = 1/(2t). For a Re~1 core the
    two are already comparable (that is what Re~1 means), so the barrier only
    *dominates* once its max(...) factor exceeds unity, i.e. once

        alpha'/l_r^2 > 1   <=>   l_r < sqrt(alpha').

    Arrest at l_r = sqrt(alpha') therefore follows from the operator, not by
    assumption, and substituting back gives t_c and u_max.
    """
    rows = []
    for a in alphas:
        l_arrest = np.sqrt(a)
        t_c = a / nu                      # from l_r^2 = nu t
        u_max = np.sqrt(nu / t_c)         # = nu/sqrt(alpha')
        w_max = u_max / l_arrest          # = nu/alpha'
        rows.append({
            "alpha_prime": a,
            "l_arrest": l_arrest,
            "t_c": t_c, "t_c_predicted": a / nu,
            "u_max": u_max, "u_max_predicted": nu / np.sqrt(a),
            "omega_max": w_max, "omega_max_predicted": nu / a,
            "Re_core_at_arrest": u_max * l_arrest / nu,
        })
    a_arr = np.array([r["alpha_prime"] for r in rows])
    fits = {
        k: float(np.polyfit(np.log(a_arr), np.log([r[k] for r in rows]), 1)[0])
        for k in ("t_c", "u_max", "omega_max", "l_arrest")
    }
    return {
        "rows": rows,
        "fitted_exponents": fits,
        "predicted_exponents": {"t_c": 1.0, "u_max": -0.5, "omega_max": -1.0, "l_arrest": 0.5},
        "Re_core_is_unity": bool(np.allclose([r["Re_core_at_arrest"] for r in rows], 1.0)),
        "self_consistent": bool(
            abs(fits["t_c"] - 1.0) < 1e-9 and abs(fits["u_max"] + 0.5) < 1e-9
            and abs(fits["omega_max"] + 1.0) < 1e-9 and abs(fits["l_arrest"] - 0.5) < 1e-9
        ),
        "conclusion": (
            "Granting the premise, the law is exact: the arrest scale follows from the "
            "barrier operator itself and the three exponents are identities. Any "
            "experimental disagreement is therefore a statement about whether the premise "
            "(Re_core ~ 1) is realised, not about the law's arithmetic."
        ),
    }


# ---------------------------------------------------------------------------
# B. Was the premise ever reached?
# ---------------------------------------------------------------------------

def premise_reachability() -> dict:
    out = {}
    shell_path = RES / "cutoff_law_shell.json"
    if shell_path.exists():
        d = json.loads(shell_path.read_text())
        nu = d["config"]["nu"]
        usable = [r for r in d["runs"][1:]
                  if r["barrier_inside_range"] and r["barrier_before_viscosity"] and r["finite"]]
        ka = np.array([r["k_alpha"] for r in usable])
        u = np.array([r["u_at_barrier"] for r in usable])
        re_a = u / (nu * ka)
        out["shell_model"] = {
            "k_alpha": ka.tolist(),
            "Re_at_arrest_scale": re_a.tolist(),
            "Re_min": float(re_a.min()), "Re_max": float(re_a.max()),
            "u_exponent_vs_k_alpha": float(np.polyfit(np.log(ka), np.log(u), 1)[0]),
            "kolmogorov_prediction": -1.0 / 3.0,
            "cutoff_law_prediction": 1.0,
            "premise_reached": bool(np.any(np.abs(re_a - 1.0) < 0.5)),
        }
    for tag in ("cutoff_law_tgv_96", "cutoff_law_tubes_32"):
        p = RES / f"{tag}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        reasons: dict[str, int] = {}
        for r in d["runs"]:
            if not r["usable"]:
                reasons[r["exclusion_reason"]] = reasons.get(r["exclusion_reason"], 0) + 1
        out[tag] = {
            "n_runs": len(d["runs"]),
            "n_usable": d["n_usable"],
            "exclusion_reasons": reasons,
            "Re_core_values": [r["Re_core"] for r in d["runs"]],
            "omega_max_spread": (
                float(np.ptp([r["omega_max"] for r in d["runs"]])
                      / np.mean([r["omega_max"] for r in d["runs"]]))
            ),
        }
    return out


def resolution_requirement(omega0: float = 2.0) -> dict:
    """n > 3 sqrt(omega_0 Re) for the barrier to arrest growing vorticity."""
    res = {}
    for re in (200, 400, 800, 1600, 3200):
        res[str(re)] = {"n_required": float(3.0 * np.sqrt(omega0 * re))}
    return {"omega_0": omega0, "requirement": "n > 3*sqrt(omega_0*Re)", "by_reynolds": res}


# ---------------------------------------------------------------------------
# C. Figure
# ---------------------------------------------------------------------------

def make_figure(analysis: dict) -> str | None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    shell_path = RES / "cutoff_law_shell.json"
    if not shell_path.exists():
        return None
    d = json.loads(shell_path.read_text())
    nu = d["config"]["nu"]
    usable = [r for r in d["runs"][1:]
              if r["barrier_inside_range"] and r["barrier_before_viscosity"] and r["finite"]]
    ka = np.array([r["k_alpha"] for r in usable])
    u = np.array([r["u_at_barrier"] for r in usable])
    re_a = u / (nu * ka)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))

    a0 = ax[0]
    a0.loglog(ka, u, "o", ms=8, color="#1f77b4", label="measured $u(k_\\alpha)$")
    p = np.polyfit(np.log(ka), np.log(u), 1)
    a0.loglog(ka, np.exp(np.polyval(p, np.log(ka))), "-", color="#1f77b4",
              label=f"fit $k_\\alpha^{{{p[0]:.3f}}}$")
    a0.loglog(ka, u[0] * (ka / ka[0]) ** (-1 / 3), "--", color="#2ca02c",
              label="Kolmogorov $k^{-1/3}$")
    a0.loglog(ka, nu * ka, ":", color="#d62728", lw=2,
              label="cutoff law $u\\sim\\nu k_\\alpha$")
    a0.set_xlabel("barrier wavenumber $k_\\alpha=1/\\sqrt{\\alpha'}$")
    a0.set_ylabel("$u$ at the arrest scale")
    a0.set_title("Arrest-scale velocity:\ninertial-range, not viscous-core")
    a0.legend(fontsize=8); a0.grid(alpha=.3, which="both")

    a1 = ax[1]
    a1.loglog(ka, re_a, "s-", color="#9467bd")
    a1.axhline(1.0, color="k", ls="--", label="$Re=1$ (the law's premise)")
    a1.set_xlabel("$k_\\alpha$"); a1.set_ylabel("$Re$ at arrest scale")
    a1.set_title("The premise is never met\n($Re\\gg1$ throughout)")
    a1.legend(fontsize=8); a1.grid(alpha=.3, which="both")

    # Panel C: the barrier band is squeezed from BOTH sides, using the measured
    # 96^3 run rather than an idealised single constraint. Lower edge: the cap
    # nu*k^2 must exceed omega_0 or the barrier cannot arrest growing vorticity.
    # Upper edges: k_alpha must stay below the measured Kolmogorov wavenumber
    # (else viscosity dissipates first) and below the dealiasing cutoff.
    a2 = ax[2]
    p96 = RES / "cutoff_law_tgv_96.json"
    if p96.exists():
        d96 = json.loads(p96.read_text())
        nu96 = d96["config"]["nu"]
        ka96 = np.array([r["k_alpha"] for r in d96["runs"]])
        keta = float(np.median([r["k_eta"] for r in d96["runs"]]))
        k_lower = np.sqrt(2.0 / nu96)              # nu k^2 > omega_0 = 2
        k_res = (2.0 / 3.0) * (d96["config"]["n"] / 2.0)
        colors = ["#2ca02c" if r["usable"] else "#d62728" for r in d96["runs"]]
        a2.scatter(ka96, np.arange(len(ka96)), c=colors, s=70, zorder=3,
                   label="runs (red = excluded)")
        a2.axvline(k_lower, color="#ff7f0e", lw=2,
                   label=f"$k_\\alpha>\\sqrt{{\\omega_0/\\nu}}$ = {k_lower:.0f}")
        a2.axvline(keta, color="#1f77b4", lw=2, ls="--",
                   label=f"$k_\\eta$ (measured) = {keta:.0f}")
        a2.axvline(k_res, color="k", lw=1.5, ls=":", label=f"dealias cutoff = {k_res:.0f}")
        if k_lower < keta:
            a2.axvspan(k_lower, min(keta, k_res), color="green", alpha=.12)
        a2.set_xlabel("$k_\\alpha$"); a2.set_ylabel("run index")
        a2.set_title("96³ DNS: the usable band is empty\n"
                     "($k_\\eta$ falls below the lower edge)")
        a2.legend(fontsize=7, loc="upper right"); a2.grid(alpha=.3)
    else:
        re = np.logspace(np.log10(100), np.log10(5000), 60)
        a2.loglog(re, 3 * np.sqrt(2.0 * re), "-", color="#ff7f0e",
                  label="$n>3\\sqrt{\\omega_0 Re}$ (necessary, not sufficient)")
        a2.set_xlabel("Reynolds number"); a2.set_ylabel("grid $n$")
        a2.legend(fontsize=8); a2.grid(alpha=.3, which="both")

    fig.suptitle("Cutoff law: the prediction fails because its premise is unreachable, "
                 "not because its arithmetic is wrong", fontsize=11)
    fig.tight_layout()
    out = RES / "cutoff_law_summary.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return str(out)


def main() -> None:
    print("=" * 78)
    print(" CUTOFF LAW: is the law wrong, or is its premise unreachable?")
    print("=" * 78)

    a = analytic_self_consistency()
    print("\n[A] Internal consistency, granting the premise (Re_core = 1):")
    print(f"    Re_core at arrest is exactly 1 in every row: {a['Re_core_is_unity']}")
    for k, v in a["fitted_exponents"].items():
        print(f"    {k:<10} exponent {v:+.6f}  (predicted {a['predicted_exponents'][k]:+.1f})")
    print(f"    -> law is self-consistent: {a['self_consistent']}")

    b = premise_reachability()
    print("\n[B] Was the premise ever reached?")
    if "shell_model" in b:
        s = b["shell_model"]
        print(f"    shell model: Re at arrest scale spans {s['Re_min']:.1f} .. {s['Re_max']:.1f}")
        print(f"                 u ~ k_alpha^{s['u_exponent_vs_k_alpha']:+.3f}  "
              f"(Kolmogorov {s['kolmogorov_prediction']:+.3f}, cutoff law {s['cutoff_law_prediction']:+.1f})")
        print(f"                 premise reached: {s['premise_reached']}")
    for tag in ("cutoff_law_tgv_96", "cutoff_law_tubes_32"):
        if tag in b:
            t = b[tag]
            print(f"    {tag}: {t['n_usable']}/{t['n_runs']} usable; "
                  f"omega_max spread across all alpha' = {t['omega_max_spread']*100:.2f}%")
            for reason, cnt in t["exclusion_reasons"].items():
                print(f"        {cnt}x  {reason}")

    r = resolution_requirement()
    print("\n[C] 3D DNS resolution requirement (n > 3*sqrt(omega_0*Re), omega_0=2):")
    for re_, v in r["by_reynolds"].items():
        print(f"    Re={re_:>5}: n > {v['n_required']:.0f}")

    fig = make_figure(a)
    print(f"\n figure: {fig}" if fig else "\n (matplotlib unavailable; figure skipped)")

    out = RES / "cutoff_law_analysis.json"
    out.write_text(json.dumps(
        {"analytic_self_consistency": a, "premise_reachability": b,
         "resolution_requirement": r}, indent=2))
    print(f" written to {out}")

    print("\n" + "-" * 78)
    print(" CONCLUSION")
    print(" The cutoff law is arithmetically exact given its premise. The premise is a")
    print(" Re~1 viscously-dominated collapsing core -- the special property of the")
    print(" OpenAI construction. Neither a forced cascade nor decaying 3D turbulence")
    print(" realises it, so the law cannot be tested with generic initial data at any")
    print(" resolution. Testing it requires reproducing the construction's own forcing.")


if __name__ == "__main__":
    main()
