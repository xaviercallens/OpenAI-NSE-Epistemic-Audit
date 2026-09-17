#!/usr/bin/env python3
"""Reynolds-number sweep of the compressible forced core: does the compressible/thermal lock
strengthen along the inertial route (Re > 1), as the regime map (Kn = Ma/Re) says it should?
Writes results/compressible_core_re_sweep.json."""
from __future__ import annotations

import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from compressible_core import Config, Core, summarize, HOLE_K

OUT = Path(__file__).parent / "results"
RES = [0.25, 1.0, 4.0, 16.0, 64.0]
MODELS = {
    "iso_muConst_mass": dict(mu_law="const"),
    "air_full_mass": dict(mu_law="T", thermo="full"),
    "iso_muConst_vol": dict(mu_law="const", force="volume"),
    "iso_muRho_mass": dict(mu_law="rho"),
}


# (model, Re, n, l_end): the sweep, then grid convergence and a deeper target at Re = 16
EXTRA = [("air_full_mass", 16.0, 1000, 0.25), ("iso_muConst_mass", 16.0, 1000, 0.25),
         ("air_full_mass", 16.0, 700, 0.125), ("iso_muConst_mass", 16.0, 700, 0.125),
         ("air_full_vol", 16.0, 500, 0.25), ("air_full_muRho_mass", 16.0, 500, 0.25)]
MODELS["air_full_vol"] = dict(mu_law="T", thermo="full", force="volume")
MODELS["air_full_muRho_mass"] = dict(mu_law="rho", thermo="full")


def run(item):
    model, re, n, l_end = item
    cfg = Config(re=re, l_end=l_end, n=n, **MODELS[model])
    rec, status = Core(cfg).run(verbose=False)
    out = summarize(cfg, rec, status)
    s = out["series"]
    l, tau = np.array(s["l_meas"]), np.array(s["tau"])
    k = max(6, len(l) // 12)
    out["collapse_rate_end"] = float(np.polyfit(np.log(tau[-k:]), np.log(l[-k:]), 1)[0])   # 0.5 = unimpeded, 0 = arrested
    out["quasi_steady_hole_at_end"] = float(np.exp(-HOLE_K * s["mach_local"][-1] ** 2))
    out["u_max_over_c_inf_end"] = s["u_max"][-1]
    tag = "" if (n, l_end) == (500, 0.25) else f"_n{n}_lend{l_end:g}"
    return f"{model}_re{re:g}{tag}", out


if __name__ == "__main__":
    items = [(m, re, 500, 0.25) for m in list(MODELS)[:4] for re in RES] + EXTRA
    with Pool(7) as pool:
        res = dict(pool.map(run, items, chunksize=1))
    (OUT / "compressible_core_re_sweep.json").write_text(json.dumps(res, indent=1))
    print(f"{'case':28s} {'status':22s} {'l_end':>6s} {'min l':>6s} {'max lag':>8s} {'rate':>6s} {'rho0':>8s} {'T0':>6s} {'Ma_loc':>6s} {'u/c_inf':>7s} {'Ma_tgt':>6s} {'Kn_loc':>7s}")
    for k, v in res.items():
        s = v["series"]
        print(f"{k:28s} {v['status'][:22]:22s} {v['l_target_end_over_Re_lstar']:6.2f} {v['min_l_meas_over_Re_lstar']:6.2f} {v['max_lag']:+8.2f} "
              f"{v['collapse_rate_end']:6.3f} {v['rho0_end']:8.2e} {v['T0_end']:6.2f} {s['mach_local'][-1]:6.2f} {v['u_max_over_c_inf_end']:7.2f} {s['mach_target'][-1]:6.2f} {s['kn_local'][-1]:7.2f}")
