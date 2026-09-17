#!/usr/bin/env python3
"""Physics ladder for compressible_core.py: one effect switched on at a time, plus controls,
Reynolds-number scaling and grid convergence. Writes results/compressible_core_study.json."""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

from compressible_core import Config, Core, summarize, HOLE_K

OUT = Path(__file__).parent / "results"

CASES = {
    # name: (kwargs, what it isolates)
    "control_lowMach":     (dict(mu_law="rho", c_scale=50.0, l_end=1.0), "c -> 50 c: incompressible limit, must track"),
    "A_iso_muRho_mass":    (dict(mu_law="rho"), "isothermal, mu ~ rho (nu const): continuum analogue of constant-tau BGK"),
    "B_iso_muConst_mass":  (dict(mu_law="const"), "isothermal, mu independent of rho: the density-hole feedback"),
    "C_iso_muConst_vol":   (dict(mu_law="const", force="volume"), "as B with force per unit volume"),
    "D_full_muT_mass":     (dict(mu_law="T", thermo="full"), "air: energy equation, mu(T), Pr 0.71, viscous heating"),
    "E_full_muT_vol":      (dict(mu_law="T", thermo="full", force="volume"), "as D with force per unit volume"),
    "F_noheat_muT_mass":   (dict(mu_law="T", thermo="noheat"), "as D without viscous heating (expansion cooling only)"),
    "G_full_muConst_mass": (dict(mu_law="const", thermo="full"), "energy equation but mu fixed: isolates mu(T)"),
    "H_full_muRho_mass":   (dict(mu_law="rho", thermo="full"), "energy equation with nu const: thermodynamics without the viscosity feedback"),
    "B_re4":               (dict(mu_law="const", re=4.0), "B at Re = 4 (tests l_c ~ Re l_star)"),
    "D_re4":               (dict(mu_law="T", thermo="full", re=4.0), "D at Re = 4"),
    "B_re025":             (dict(mu_law="const", re=0.25), "B at Re = 0.25"),
    "B_n800":              (dict(mu_law="const", n=800), "B, grid convergence"),
    "D_n800":              (dict(mu_law="T", thermo="full", n=800), "D, grid convergence"),
}


def run(item):
    name, (kw, what) = item
    cfg = Config(**kw)
    rec, status = Core(cfg).run(verbose=False)
    out = summarize(cfg, rec, status)
    out["what"] = what
    return name, out


if __name__ == "__main__":
    with Pool(6) as pool:
        res = dict(pool.map(run, CASES.items(), chunksize=1))
    res["_prediction"] = {"hole_coefficient": HOLE_K, "Ma_c": (0.2231435513 / HOLE_K) ** 0.5,
                          "l_c_over_Re_lstar": (HOLE_K / 0.2231435513) ** 0.5}
    (OUT / "compressible_core_study.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if k.startswith("_"):
            continue
        f = lambda x: "  none" if x is None else f"{x:6.2f}"
        print(f"{k:22s} {v['status'][:24]:24s} l(lag10)={f(v['l_at_lag10_over_Re_lstar'])} l(lag50)={f(v['l_at_lag50_over_Re_lstar'])} "
              f"min l={v['min_l_meas_over_Re_lstar']:6.2f} lag[min,max]=[{v['min_lag']:+.3f},{v['max_lag']:+.2f}] rho0={v['rho0_end']:.3g} T0={v['T0_end']:.3f} Tmax={v['T_max']:.3f} dM={v['mass_drift_inner']:.1e}")
