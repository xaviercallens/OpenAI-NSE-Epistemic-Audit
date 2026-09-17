#!/usr/bin/env python3
"""Continuum (1D compressible Navier-Stokes-Fourier) prediction for the MD forced core of md_core_rs.

Monatomic ideal gas (gamma = 5/3, Pr = 2/3, mu ~ T^s), same Reynolds number, same start and end core
sizes, and the far-field sponge placed where the MD thermostat buffer starts (3.2 l_start). Inputs in LJ
units: nu and c of the MD gas, so l* = nu/c. Writes results/compressible_core_md_match.json.

  python3 compressible_core_md_match.py --nu 1.41 --c 1.826 --l-start 40 --l-end 4 --re 4 16 32
"""
from __future__ import annotations

import argparse
import json
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from compressible_core import Config, Core, summarize

OUT = Path(__file__).parent / "results"


def run(job):
    re, lstar, a = job
    out = {}
    for tag, r_max in (("buffer_3.2", 4.0), ("wide_14", 14.0)):
        cfg = Config(re=re, mu_law="T", thermo="full", gamma=5.0 / 3.0, prandtl=2.0 / 3.0, mu_exp=a.mu_exp,
                     l_start=a.l_start / (re * lstar), l_end=a.l_end / (re * lstar), r_max=r_max, n=a.n)
        rec, status = Core(cfg).run(n_samples=160, verbose=False)
        s = summarize(cfg, rec, status)
        ser = s["series"]
        out[tag] = {"status": status,
                    "mach_target": ser["mach_target"], "mach_local": ser["mach_local"],
                    "rho0": ser["rho0"], "T0": ser["T0"], "kn_local": ser["kn_local"],
                    "l_meas_over_l_target": (np.array(ser["l_meas"]) / np.array(ser["l_target"])).tolist(),
                    "l_target_sigma": (np.array(ser["l_target"]) * lstar).tolist()}
    return f"re{re:g}", out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--nu", type=float, default=1.41)
    ap.add_argument("--c", type=float, default=1.826)
    ap.add_argument("--l-start", type=float, default=40.0)
    ap.add_argument("--l-end", type=float, default=4.0)
    ap.add_argument("--re", type=float, nargs="+", default=[4.0, 16.0, 32.0])
    ap.add_argument("--mu-exp", type=float, default=0.75)
    ap.add_argument("--n", type=int, default=500)
    a = ap.parse_args()
    lstar = a.nu / a.c
    with Pool(min(3, len(a.re))) as pool:
        res = dict(pool.map(run, [(re, lstar, a) for re in a.re]))
    res["_inputs"] = {"nu": a.nu, "c": a.c, "l_star_sigma": lstar, "l_start_sigma": a.l_start, "l_end_sigma": a.l_end,
                      "gamma": 5 / 3, "prandtl": 2 / 3, "mu_exp": a.mu_exp,
                      "note": "ideal monatomic gas; the MD gas at rho = 0.15 is mildly non-ideal"}
    (OUT / "compressible_core_md_match.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if k.startswith("_"):
            continue
        for tag, o in v.items():
            mt, ml = np.array(o["mach_target"]), np.array(o["mach_local"])
            row = " ".join(f"{m:.1f}:{ml[int(np.argmin(abs(mt - m)))]:.2f}" for m in (0.5, 1, 1.5, 2, 3) if m <= mt.max() * 1.01)
            print(f"{k:5s} {tag:10s} {o['status'][:16]:16s} target:local Mach  {row}   rho0_end={o['rho0'][-1]:.3f} T0_end={o['T0'][-1]:.2f}")
