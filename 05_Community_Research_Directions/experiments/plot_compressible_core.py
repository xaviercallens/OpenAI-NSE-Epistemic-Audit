#!/usr/bin/env python3
"""Figure for the compressible/thermal forced-core study: results/compressible_core.png."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

R = Path(__file__).parent / "results"
d = json.load(open(R / "compressible_core_re_sweep.json"))
fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))

styles = {"iso_muRho_mass": ("nu const, isothermal (BGK const-tau analogue)", "tab:gray", "--"),
          "iso_muConst_vol": ("real-gas mu, isothermal, force / volume", "tab:orange", "-."),
          "iso_muConst_mass": ("real-gas mu, isothermal, force / mass", "tab:blue", "-"),
          "air_full_vol": ("air, full thermodynamics, force / volume", "tab:purple", "-."),
          "air_full_mass": ("air, full thermodynamics, force / mass", "tab:red", "-")}
for m, (lab, col, ls) in styles.items():
    s = d[f"{m}_re16"]["series"]
    ax[0].loglog(s["mach_target"], s["mach_local"], color=col, ls=ls, label=lab)
for key, col in (("air_full_mass_re16_n700_lend0.125", "tab:red"), ("iso_muConst_mass_re16_n700_lend0.125", "tab:blue")):
    s = d[key]["series"]
    ax[0].loglog(s["mach_target"], s["mach_local"], color=col, lw=0.8, alpha=0.6)
x = np.array([0.03, 8]); ax[0].loglog(x, x, "k:", lw=0.8, label="incompressible target")
ax[0].set_xlabel("target Mach number  Re l*/l"); ax[0].set_ylabel("actual peak local Mach number")
ax[0].set_title("Re = 16: the Mach number locks"); ax[0].legend(fontsize=7); ax[0].set_ylim(0.03, 8)

res = [0.25, 1, 4, 16, 64]
for m in ("iso_muRho_mass", "iso_muConst_vol", "iso_muConst_mass", "air_full_mass"):
    lab, col, ls = styles[m]
    ax[1].semilogx(res, [d[f"{m}_re{r:g}"]["series"]["mach_local"][-1] for r in res], "o", color=col, ls=ls, label=lab)
ax[1].axhline(4, color="k", ls=":", lw=0.8); ax[1].text(0.27, 4.1, "target Ma = 4", fontsize=8)
ax[1].set_xlabel("core Reynolds number"); ax[1].set_ylabel("peak local Mach at target Ma = 4")
ax[1].set_title("the lock strengthens along the inertial route"); ax[1].legend(fontsize=7)

s = d["air_full_mass_re16_n700_lend0.125"]["series"]
ax[2].loglog(s["mach_target"], s["T0"], "tab:red", label="core temperature T0 / T_inf")
ax[2].loglog(s["mach_target"], s["rho0"], "tab:blue", label="core density rho0 / rho_inf")
ax[2].loglog(s["mach_target"], s["nu0_over_nu"], "tab:green", label="core kinematic viscosity nu0 / nu_inf")
ax[2].loglog(s["mach_target"], np.array(s["l_meas"]) / np.array(s["l_target"]), "k", label="core size / target")
ax[2].set_xlabel("target Mach number"); ax[2].set_title("air, Re = 16: what the core does instead"); ax[2].legend(fontsize=7)
for a in ax:
    a.grid(alpha=0.3, which="both")
fig.tight_layout(); fig.savefig(R / "compressible_core.png", dpi=130)
print("written", R / "compressible_core.png")
