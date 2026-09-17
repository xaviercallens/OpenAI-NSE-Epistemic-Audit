"""
Figure for the kinetic-lock collapse test (kinetic_lock_rs).

Reads   results/kinetic_lock_gates.json, results/kinetic_lock_collapse.json,
        results/lock_k_kinetic_spectrum.json
Writes  results/kinetic_lock.png

Panels
  1  G4: solver decay rate of the shear wave vs exact BGK, Q = 12/16/24
  2  lag of the kinetic core (solid) and NSE control (dotted) vs l_target/lambda,
     lambda = 0.065 at three grids
  3  resolution: l_kin/lambda at the lag > 10% crossing and the estimator grid floor vs dx/lambda
  4  (a) l_arrest vs lambda: fixed dx/lambda sweep and fixed-grid (N = 288) sweep
  5  (b) k_omega*lambda at the lag crossing vs dx/lambda, against sqrt(pi/2)
  6  Mach (solid) and negative-mass fraction (dashed) along the collapse
All numbers are read from the JSON files; nothing is recomputed except the plot.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np

RES = Path(__file__).parent / "results"
COL = {1.0: "C3", 0.25: "C0"}


def main() -> None:
    gates = json.loads((RES / "kinetic_lock_gates.json").read_text())
    coll = json.loads((RES / "kinetic_lock_collapse.json").read_text())
    spec = json.loads((RES / "lock_k_kinetic_spectrum.json").read_text())["series"]
    sqrt_pi_2 = coll["definitions"]["sqrt_pi_over_2"]
    term24 = next(t["lattice_termination_q"] for t in gates["G4"]["terminations"] if t["Q"] == 24)

    fig, ax = plt.subplots(2, 3, figsize=(17, 10))
    ax = ax.ravel()

    # 1  G4
    a = ax[0]
    rows = gates["G4"]["rows"]
    for Q, mk in [(12, "s"), (16, "^"), (24, "o")]:
        rq = [r for r in rows if r["Q"] == Q]
        a.plot([r["q"] for r in rq], [r["solver_gamma_tau"] for r in rq], mk, mfc="none", ms=7,
               label=f"solver, Q={Q}")
    qs = np.array(spec["q"], dtype=float)
    g1 = np.array([np.nan if x is None else x for x in spec["gamma_tau_M1"]], dtype=float)
    ok = qs <= 2.2
    a.plot(qs[ok], g1[ok], "k-", lw=1.5, label="exact BGK (M1)")
    a.plot(qs[ok], qs[ok] ** 2, "k:", lw=1, label=r"NSE $\nu k^2$")
    for t in gates["G4"]["terminations"]:
        a.axvline(t["lattice_termination_q"], color="0.75", lw=0.8)
    a.axvline(sqrt_pi_2, color="r", lw=1, ls="--", label=r"$\sqrt{\pi/2}$")
    a.set_xscale("log"); a.set_yscale("log"); a.set_ylim(1e-3, 3)
    a.set_xlabel(r"$q=k\lambda$"); a.set_ylabel(r"$-\mathrm{Re}\,s\,\tau$")
    a.set_title(f"G4 shear wave, dt=tau*{gates['G4']['dt_over_tau']} (grey: lattice termination)", fontsize=9)
    a.legend(fontsize=7)

    all_runs = coll["runs_main"] + coll["runs_fixed_grid"] + coll["runs_fine"] + coll["runs_extra"]
    ladder_runs = [r for r in all_runs
                   if abs(r["lambda"] - 0.065) < 1e-9 and r["Q"] == 24 and abs(r["l_start_over_lambda"] - 4) < 1e-9]
    ladder_runs.sort(key=lambda r: (r["re_core"], r["N"]))
    ls_for_n = {144: ":", 288: "--", 576: "-"}

    # 2  lag
    a = ax[1]
    for r in ladder_runs:
        s = r["series"]
        re = float(r["re_core"])
        lt = np.maximum(np.array(s["ell_target_over_lambda"]), 1e-2)
        a.plot(lt, s["lag"], color=COL[re], ls=ls_for_n.get(r["N"], "-"), lw=1.2,
               label=f"kinetic Re={re:g} N={r['N']}")
        a.plot(lt, s["nse_lag_on_kinetic_times"], color="0.4", ls=ls_for_n.get(r["N"], "-"), lw=0.6)
    a.axhline(0.10, color="k", lw=0.8)
    a.axvline(sqrt_pi_2 ** -1 * np.sqrt(2), color="r", lw=0.8, ls="--")
    a.set_xscale("log"); a.invert_xaxis(); a.set_ylim(-0.25, 0.6); a.set_xlim(5, 0.15)
    a.set_xlabel(r"$\ell_{target}/\lambda$"); a.set_ylabel(r"lag $=\ell_{kin}/\ell_{ref}-1$")
    a.set_title(r"lag at $\lambda$=0.065 (grey: NSE control); red dashes: Gaussian with $k_\omega\lambda=\sqrt{\pi/2}$", fontsize=9)
    a.legend(fontsize=7)

    # 3  resolution ladder
    a = ax[2]
    for L in coll["resolution_ladders"]:
        if abs(L["lambda"] - 0.065) > 1e-9 or L["Q"] != 24:
            continue
        re = float(L["re_core"])
        dx = np.array(L["dx_over_lambda"], dtype=float)
        a.plot(dx, L["ell_kin_over_lambda_at_lag_crossing"], "o-", color=COL[re], label=f"l_kin at lag>10%, Re={re:g}")
        a.plot(dx, L["min_windowed_ell_over_lambda"], "s:", color=COL[re], mfc="none", label=f"min windowed l, Re={re:g}")
        a.plot(dx, L["grid_floor_over_lambda"], "k^--", mfc="none", lw=0.8,
               label="estimator grid floor" if re == 1.0 else None)
    a.axhline(np.sqrt(2) / sqrt_pi_2, color="r", ls="--", lw=0.8, label=r"Gaussian at $k_\omega\lambda=\sqrt{\pi/2}$")
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlabel(r"$\Delta x/\lambda$"); a.set_ylabel(r"$\ell/\lambda$")
    a.set_title(r"resolution ladder, $\lambda$=0.065 (N=144, 288, 576)", fontsize=9)
    a.legend(fontsize=7)

    # 4  (a) arrest scale vs lambda
    a = ax[3]
    for key, mk, lab in [("main_sweep", "o", "dx/lambda fixed"), ("fixed_grid_sweep", "D", "N=288 fixed")]:
        runs = coll["runs_main"] if key == "main_sweep" else coll.get("runs_fixed_grid", [])
        for re in (1.0, 0.25):
            rr = sorted([r for r in runs if float(r["re_core"]) == re], key=lambda r: r["lambda"])
            if not rr:
                continue
            lam = np.array([r["lambda"] for r in rr])
            la = np.array([r["ell_arrest"] for r in rr])
            blk = coll[key]["by_re"].get(f"re_core_{re:g}", coll[key]["by_re"].get(f"re_core_{re}"))
            fit = blk["a_exponent_min_ell_kin"] if blk else {}
            txt = ""
            if fit and fit.get("slope") is not None:
                txt = f": slope {fit['slope']:.2f} [{fit['ci95'][0]:.2f},{fit['ci95'][1]:.2f}]"
            a.plot(lam, la, mk + ("-" if key == "main_sweep" else "--"), color=COL[re], mfc="none" if mk == "D" else COL[re],
                   label=f"Re={re:g}, {lab}{txt}")
    a.set_xscale("log"); a.set_yscale("log")
    a.set_xlabel(r"$\lambda=\tau$"); a.set_ylabel(r"$\ell_{arrest}=\min\,\ell_{kin}$")
    a.set_title("(a) arrest scale", fontsize=9); a.legend(fontsize=7)

    # 5  (b) k_omega lambda at lag crossing vs resolution
    a = ax[4]
    for L in coll["resolution_ladders"]:
        if abs(L["lambda"] - 0.065) > 1e-9 or L["Q"] != 24:
            continue
        re = float(L["re_core"])
        a.plot(L["dx_over_lambda"], L["k_omega_lambda_at_lag_crossing"], "o-", color=COL[re], label=f"lambda=0.065, Re={re:g}")
    for r in coll["runs_main"] + coll.get("runs_fixed_grid", []) + coll.get("runs_fine", []):
        if r["at_lag_crossing"]:
            a.plot(r["dx_over_lambda"], r["at_lag_crossing"]["k_omega_lambda"], "x", color=COL[float(r["re_core"])])
    a.axhline(sqrt_pi_2, color="r", ls="--", label=r"$\sqrt{\pi/2}$ (exact BGK termination)")
    a.axhline(term24, color="0.5", ls=":", label="Q=24 lattice termination")
    a.set_xscale("log"); a.set_xlabel(r"$\Delta x/\lambda$"); a.set_ylabel(r"$k_\omega\lambda$ at lag > 10%")
    a.set_title("(b) spectral centroid at arrest (x: sweep runs)", fontsize=9); a.legend(fontsize=7)

    # 6  Mach, negativity
    a = ax[5]
    for r in ladder_runs:
        s = r["series"]
        re = float(r["re_core"])
        lt = np.maximum(np.array(s["ell_target_over_lambda"]), 1e-2)
        a.plot(lt, s["mach"], color=COL[re], ls=ls_for_n.get(r["N"], "-"), lw=1.2)
        a.plot(lt, np.maximum(np.array(s["negative_mass_fraction"]), 1e-16), color=COL[re],
               ls=ls_for_n.get(r["N"], "-"), lw=0.6, alpha=0.6)
    a.axhline(1e-6, color="k", lw=0.8, ls=":")
    a.axhline(1.0, color="k", lw=0.5)
    a.set_xscale("log"); a.set_yscale("log"); a.invert_xaxis(); a.set_ylim(1e-12, 10); a.set_xlim(5, 0.15)
    a.set_xlabel(r"$\ell_{target}/\lambda$")
    a.set_title("Mach (upper curves), negative-mass fraction (lower); dotted = G5 tolerance", fontsize=9)

    for a in ax:
        a.tick_params(which="minor", labelsize=6)
    fig.tight_layout()
    out = RES / "kinetic_lock.png"
    fig.savefig(out, dpi=120)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
