"""
Figure for the forced-core test bed (Direction 1).

Three panels:
  A  core radius l(t) for every alpha' against the analytic target -- the control
     (alpha'=0) must lie on the target; barrier runs must lag it.
  B  the mechanism: B/F against alpha'/(nu tau), pooled over runs and samples,
     with the fitted power law and the predicted unit slope. Runs that reach
     B/F = 1 (arrest) are marked.
  C  arrest-point exponents, if >= 3 runs crossed: measured tau_c, l, u, omega at
     the crossing against alpha', with the predicted power laws (which include
     the measured prefactor C).

Usage:  python3 plot_forced_core.py results/forced_core_96_v3.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np


def main(path: str) -> str | None:
    d = json.loads(Path(path).read_text())
    nu = d["config"]["nu"]
    law = d.get("mechanism_bf_law", {})
    C = law.get("prefactor_C", np.nan)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))

    # --- A: l(t) vs target --------------------------------------------------
    a = ax[0]
    ctrl = d["series"]["None"]
    a.plot(ctrl["tau"], ctrl["ell_target"], "k-", lw=2, label="target $\\sqrt{\\nu\\tau}$")
    a.plot(ctrl["tau"], ctrl["ell_meas"], "k--", lw=1, label="control $\\alpha'=0$")
    for r in d["runs"]:
        S = d["series"][str(r["alpha_prime"])]
        a.plot(S["tau"], S["ell_meas"], "-", label=f"$\\alpha'$={r['alpha_prime']:.3g}")
        if r["arrested_before_end"]:
            a.plot([r["tau_at_arrest"]], [r["ell_at_arrest"]], "o", ms=7, color="k")
    a.set_xscale("log"); a.set_yscale("log"); a.invert_xaxis()
    a.set_xlabel("time to blow-up $\\tau$"); a.set_ylabel("core radius $\\ell$")
    a.set_title("A. Forced Re=1 core: control tracks target,\nbarrier runs lag it (dots: B/F=1 crossing)")
    a.legend(fontsize=7); a.grid(alpha=.3, which="both")

    # --- B: the mechanism ----------------------------------------------------
    b = ax[1]
    xs, ys = [], []
    for r in d["runs"]:
        S = d["series"][str(r["alpha_prime"])]
        bf = np.asarray(S["barrier_extra"]) / np.maximum(np.abs(np.asarray(S["forcing_power"])), 1e-300)
        x = r["alpha_prime"] / (nu * np.asarray(S["tau"]))
        m = bf > 0.02
        b.loglog(x[m], bf[m], ".", ms=4, label=f"$\\alpha'$={r['alpha_prime']:.3g}")
        xs.append(x[m]); ys.append(bf[m])
    if "slope" in law:
        x_all = np.concatenate(xs)
        xr = np.array([x_all.min(), x_all.max()])
        b.loglog(xr, C * xr ** law["slope"], "k-", lw=2,
                 label=f"fit: slope {law['slope']:+.2f}, C={C:.2f}")
        b.loglog(xr, C * xr, "r--", lw=1.5, label="predicted slope +1")
    b.axhline(1.0, color="gray", ls=":", label="B/F = 1 (arrest)")
    b.set_xlabel("$\\alpha'/(\\nu\\tau)$"); b.set_ylabel("barrier dissipation / forcing power")
    coll = (f"collapse: per-run C spread {100*law['C_spread_rel']:.0f}%"
            if "C_spread_rel" in law else "")
    b.set_title(f"B. Mechanism: $B/F$ is a function of $\\alpha'/(\\nu\\tau)$ alone\n{coll}")
    b.legend(fontsize=7); b.grid(alpha=.3, which="both")

    # --- C: arrest exponents -------------------------------------------------
    c = ax[2]
    arr = [r for r in d["runs"] if r["arrested_before_end"]]
    if len(arr) >= 3 and d.get("fits"):
        al = np.array([r["alpha_prime"] for r in arr])
        spec = [("tau_at_arrest", "$\\tau_c$", 1.0, lambda A: C * A / nu),
                ("ell_at_arrest", "$\\ell_c$", 0.5, lambda A: np.sqrt(C * A)),
                ("u_at_arrest", "$u_c$", -0.5, lambda A: nu / np.sqrt(C * A)),
                ("omega_at_arrest", "$\\omega_c$", -1.0, lambda A: d["control"]["gamma"] / (np.pi * C * A))]
        for key, lab, pexp, pred in spec:
            y = np.array([r[key] for r in arr])
            f = d["fits"].get(key, {})
            line, = c.loglog(al, y / y[0], "o-", label=f"{lab}: fit {f.get('exponent', np.nan):+.2f} (pred {pexp:+.1f})")
            c.loglog(al, pred(al) / pred(al[0]), "--", color=line.get_color(), alpha=.6)
        c.set_xlabel("$\\alpha'$"); c.set_ylabel("normalised to first point")
        c.set_title(f"C. Arrest-point scalings ({len(arr)} runs crossed B/F=1)\nsolid: measured, dashed: predicted with measured C")
        c.legend(fontsize=7)
    else:
        c.text(0.5, 0.5, f"{len(arr)} run(s) reached B/F = 1\n(need >= 3 for exponent fits)\n"
               f"predicted crossover $\\tau_c = C\\alpha'/\\nu$ with C = {C:.2f}",
               ha="center", va="center", transform=c.transAxes, fontsize=10)
        c.set_title("C. Arrest-point scalings"); c.set_axis_off()
    c.grid(alpha=.3, which="both")

    fig.suptitle("Forced-core test bed: the cutoff law tested with its premise satisfied by construction",
                 fontsize=11)
    fig.tight_layout()
    out = Path(path).with_suffix(".png")
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(out)


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "results/forced_core_32_v3.json"
    print(main(p) or "(matplotlib unavailable)")
