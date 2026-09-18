#!/usr/bin/env python3
"""Analysis of the molecular-dynamics forced-core runs (md_core_rs): gates, viscosity, Mach-lock series.

Reads md_core_rs/runs/*.json (raw, not committed) and writes
    results/md_core_gates.json   gates M1-M5 (NVE drift, equilibrium EOS check, sound speed, viscosity, buffer)
    results/md_core_runs.json    ensemble series and tables of the forced runs (gas and liquid)
    results/md_core.png          figure

LJ units (sigma = eps = m = k_B = 1), truncated-shifted potential, r_c = 2.5.

Estimators, and their known biases
----------------------------------
* u_theta(r), T(r), rho(r) are azimuthal/axial bin averages over a time window (the run file says how many
  particles per bin per sample). T is the temperature of the peculiar motion about the bin-mean velocity.
* peak swirl and peak local Mach number are reported three ways:
    raw     max over bins                         -- biased UPWARD by noise (a maximum of noisy values);
    smooth  max over a 3-bin count-weighted mean   -- less biased, slightly smeared;
    fit     from a two-parameter Lamb-Oseen fit (Gamma_fit, l_fit): u_peak = PEAK Gamma_fit / (2 pi l_fit),
            divided by sqrt(gamma T) at the fitted peak radius -- unbiased if the profile is Lamb-Oseen, which
            a compressible core need not be.
  The ensemble standard error (std / sqrt(n_seeds)) is attached to every quoted number.
* local sound speed c_loc = sqrt(gamma T_loc) with gamma = 5/3: an ideal-gas approximation (the gas at
  rho = 0.15, T = 2 has compressibility factor ~0.9); the far-field c from the virial EOS is reported beside it.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
RUNS = HERE.parent / "md_core_rs" / "runs"
OUT = HERE / "results"
PEAK = 0.6381726863389515
X_PEAK = 1.1209064227785254          # r_peak / l for a Lamb-Oseen vortex
RC = 2.5
GAMMA = 5.0 / 3.0
OMEGA22_T2 = 1.175                   # LJ collision integral Omega(2,2)* at T* = 2 (tabulated)


# ----------------------------------------------------------------------------------------------------------
# virial coefficients of the truncated-shifted LJ potential, EOS, sound speed, Enskog viscosity
# ----------------------------------------------------------------------------------------------------------
def u_ts(r):
    sh = 4.0 * (RC ** -12 - RC ** -6)
    return np.where(r < RC, 4.0 * (r ** -12 - r ** -6) - sh, 0.0)


def mayer(r, T, potential=u_ts):
    with np.errstate(over="ignore"):
        return np.exp(-np.clip(potential(r) / T, -700, 700)) - 1.0


def b2(T, potential=u_ts, rmax=RC, n=20000):
    r = (np.arange(n) + 0.5) * rmax / n
    return float(-2.0 * np.pi * np.sum(mayer(r, T, potential) * r * r) * rmax / n)


def b3(T, potential=u_ts, rmax=RC, n=1500):
    """B3 = -(8 pi^2 / 3) int int f(r) f(s) r s [ int_{|r-s|}^{r+s} f(t) t dt ] dr ds  (f = 0 beyond rmax)."""
    h = rmax / n
    r = (np.arange(n) + 0.5) * h
    f = mayer(r, T, potential)
    F = np.concatenate(([0.0], np.cumsum(f * r) * h))          # F(x) = int_0^x f t dt at x = k h
    Fi = lambda x: np.interp(np.minimum(x, rmax), np.arange(n + 1) * h, F)
    R, S = np.meshgrid(r, r, indexing="ij")
    inner = Fi(R + S) - Fi(np.abs(R - S))
    return float(-(8.0 * np.pi ** 2 / 3.0) * np.sum(np.outer(f * r, f * r) * inner) * h * h)


def eos(rho, T, dT=0.02):
    """Virial EOS to third order: pressure, isothermal and adiabatic sound speed, residual c_v."""
    B = {t: (b2(t), b3(t)) for t in (T - dT, T, T + dT)}
    B2, B3 = B[T]
    dB2 = (B[T + dT][0] - B[T - dT][0]) / (2 * dT)
    dB3 = (B[T + dT][1] - B[T - dT][1]) / (2 * dT)
    d2B2 = (B[T + dT][0] - 2 * B2 + B[T - dT][0]) / dT ** 2
    d2B3 = (B[T + dT][1] - 2 * B3 + B[T - dT][1]) / dT ** 2
    Z2, Z3 = 1 + B2 * rho, 1 + B2 * rho + B3 * rho ** 2
    dp_drho = T * (1 + 2 * B2 * rho + 3 * B3 * rho ** 2)
    dp_dT = rho * Z3 + rho * T * (dB2 * rho + dB3 * rho ** 2)
    cv = 1.5 - rho * (2 * T * dB2 + T ** 2 * d2B2) - 0.5 * rho ** 2 * (2 * T * dB3 + T ** 2 * d2B3)
    c2 = dp_drho + T / (rho ** 2 * cv) * dp_dT ** 2
    # modified Enskog theory for the viscosity
    b0 = B2 + T * dB2
    y = dp_dT / rho - 1.0                                   # = b rho chi
    eta0 = (5.0 / 16.0) * np.sqrt(T / np.pi) / OMEGA22_T2
    eta = eta0 * b0 * rho * (1.0 / y + 0.8 + 0.761 * y)
    return {"B2": B2, "B3": B3, "p_B2": rho * T * Z2, "p_B2_B3": rho * T * Z3, "Z_B2_B3": Z3,
            "c_adiabatic": float(np.sqrt(c2)), "c_ideal_sqrt_gamma_T": float(np.sqrt(GAMMA * T)), "cv": cv,
            "gamma_eff_c2_over_dpdrhoT": c2 / dp_drho,
            "eta_chapman_enskog": eta0, "eta_modified_enskog": eta, "nu_chapman_enskog": eta0 / rho,
            "nu_modified_enskog": eta / rho, "mean_free_path": 1.0 / (np.sqrt(2) * np.pi * rho)}


# ----------------------------------------------------------------------------------------------------------
# run files
# ----------------------------------------------------------------------------------------------------------
def load(path):
    d = json.loads(Path(path).read_text())
    if d.get("mode") == "vortex":
        e = np.array(d["bin_edges"])
        d["r"] = 0.5 * (e[1:] + e[:-1])
        d["vol"] = np.pi * (e[1:] ** 2 - e[:-1] ** 2) * d["Lz"]
        for w in d["windows"]:
            for k in ("n_per_sample", "rho", "u_theta", "u_r", "T"):
                w[k] = np.array([np.nan if v is None else v for v in w[k]], dtype=float)
    return d


def lamb_oseen(r, gamma, l):
    return gamma / (2 * np.pi * r) * (-np.expm1(-(r / l) ** 2))


def fit_lamb_oseen(r, u, w, gamma=None, l_lo=0.5, l_hi=200.0):
    """Weighted least squares for l (and Gamma if gamma is None, solved linearly for each trial l)."""
    ok = np.isfinite(u) & (w > 0)
    r, u, w = r[ok], u[ok], w[ok]

    def cost(l):
        shape = lamb_oseen(r, 1.0, l)
        g = gamma if gamma is not None else np.sum(w * shape * u) / np.sum(w * shape * shape)
        return np.sum(w * (u - g * shape) ** 2), g

    ls = np.geomspace(l_lo, l_hi, 160)
    c = [cost(l)[0] for l in ls]
    i = int(np.argmin(c))
    lo, hi = ls[max(i - 1, 0)], ls[min(i + 1, len(ls) - 1)]
    for _ in range(60):                                        # golden-section refinement
        a, b = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
        if cost(a)[0] < cost(b)[0]:
            hi = b
        else:
            lo = a
    l = 0.5 * (lo + hi)
    return l, cost(l)[1]


def smooth3(v, w):
    v0 = np.where(np.isfinite(v), v, 0.0)
    w0 = np.where(np.isfinite(v), w, 0.0)
    num = np.convolve(v0 * w0, [1, 1, 1], mode="same")
    den = np.convolve(w0, [1, 1, 1], mode="same")
    return np.where(den > 0, num / np.maximum(den, 1e-300), np.nan)


def window_metrics(d, w, gamma_gas=GAMMA, min_particles=30.0):
    r, vol = d["r"], d["vol"]
    inside = r < d["R_b"]
    n_tot = w["n_per_sample"] * w["samples"]                   # particles accumulated in the window
    good = inside & (n_tot >= min_particles) & np.isfinite(w["u_theta"])
    u, T, rho = w["u_theta"], w["T"], w["rho"]
    out = {"t": w["t_mid"], "l_target": w["l_target"]}
    if good.sum() < 4:
        return None
    l_fix, _ = fit_lamb_oseen(r[good], u[good], n_tot[good], gamma=d["Gamma"])
    l_fit, g_fit = fit_lamb_oseen(r[good], u[good], n_tot[good])
    us, Ts = smooth3(u, n_tot), smooth3(T, n_tot)
    mach = u / np.sqrt(gamma_gas * T)
    mach_s = us / np.sqrt(gamma_gas * Ts)
    ib = int(np.nanargmax(np.where(good, u, -np.inf)))
    out.update({
        "l_fit_gamma_fixed": l_fix, "l_fit": l_fit, "gamma_fit_over_gamma": g_fit / d["Gamma"],
        "u_peak_raw": float(np.nanmax(u[good])), "r_peak_raw": float(r[ib]),
        "u_peak_smooth": float(np.nanmax(us[good])),
        "u_peak_fit": PEAK * g_fit / (2 * np.pi * l_fit),
        "mach_peak_raw": float(np.nanmax(mach[good])), "mach_peak_smooth": float(np.nanmax(mach_s[good])),
    })
    # fit-based Mach: fitted peak speed over sqrt(gamma T) at the fitted peak radius
    T_at = np.interp(X_PEAK * l_fit, r[good], Ts[good])
    out["mach_peak_fit"] = out["u_peak_fit"] / np.sqrt(gamma_gas * T_at)
    core = inside & (r < max(0.5 * l_fit, r[0] + 1e-9))
    if not core.any():
        core = np.zeros_like(inside)
        core[0] = True
    cnt = np.nansum(w["n_per_sample"][core])
    out["rho0_over_rho_inf"] = float(cnt / vol[core].sum() / d["rho"])
    tw = n_tot[core] * np.where(np.isfinite(T[core]), 1.0, 0.0)
    out["T0_over_T_inf"] = float(np.nansum(T[core] * tw) / max(tw.sum(), 1e-300) / d["T_inf"]) if tw.sum() > 0 else np.nan
    out["core_particles_in_window"] = float(n_tot[core].sum())
    lam_inf = 1.0 / (np.sqrt(2) * np.pi * d["rho"])
    out["kn_local"] = lam_inf / max(out["rho0_over_rho_inf"], 1e-6) / l_fit
    far = inside & (r > 0.6 * d["R_b"])
    tw = n_tot[far]
    out["T_inner_mean_over_T_inf"] = float(np.nansum(T[inside] * n_tot[inside]) / np.nansum(n_tot[inside] * np.isfinite(T[inside])) / d["T_inf"])
    out["far_swirl_over_lamb_oseen"] = float(np.nansum(u[far] * tw) / np.nansum(lamb_oseen(r[far], d["Gamma"], l_fix) * tw))
    return out


def series(d):
    rows = [m for m in (window_metrics(d, w) for w in d["windows"]) if m]
    return {k: np.array([row[k] for row in rows]) for k in rows[0]}


def ensemble(runs, keys):
    """mean and standard error over seeds on the common window grid (windows are deterministic in time)."""
    ss = [series(d) for d in runs]
    n = min(len(s["t"]) for s in ss)
    out = {"n_seeds": len(ss), "t": ss[0]["t"][:n].tolist(), "l_target": ss[0]["l_target"][:n].tolist()}
    for k in keys:
        a = np.array([s[k][:n] for s in ss])
        out[k] = np.nanmean(a, axis=0).tolist()
        out[k + "_se"] = (np.nanstd(a, axis=0, ddof=1) / np.sqrt(len(ss))).tolist() if len(ss) > 1 else [None] * n
    return out


KEYS = ["l_fit", "l_fit_gamma_fixed", "gamma_fit_over_gamma", "u_peak_raw", "u_peak_smooth", "u_peak_fit",
        "mach_peak_raw", "mach_peak_smooth", "mach_peak_fit", "rho0_over_rho_inf", "T0_over_T_inf", "kn_local",
        "T_inner_mean_over_T_inf", "far_swirl_over_lamb_oseen", "core_particles_in_window"]


def viscosity_from_decay(runs, skip=2):
    """l^2(t) = l0^2 + 4 nu t from the Gamma-fixed Lamb-Oseen fit; first `skip` windows dropped (sound)."""
    per = []
    for d in runs:
        s = series(d)
        t, l2 = s["t"][skip:], s["l_fit_gamma_fixed"][skip:] ** 2
        slope, icpt = np.polyfit(t, l2, 1)
        per.append({"seed": d["seed"], "nu": slope / 4.0, "l0_fit": float(np.sqrt(icpt)),
                    "rms_residual_l2": float(np.sqrt(np.mean((l2 - (slope * t + icpt)) ** 2)))})
    nus = np.array([p["nu"] for p in per])
    return {"per_seed": per, "nu_mean": float(nus.mean()),
            "nu_se": float(nus.std(ddof=1) / np.sqrt(len(nus))) if len(nus) > 1 else None}


def table(ens, mach_targets, c_inf, re, nu):
    lt = np.array(ens["l_target"])
    mt = re * nu / lt / c_inf
    rows = []
    for m in mach_targets:
        if m < mt.min() or m > mt.max():
            continue
        i = int(np.argmin(np.abs(mt - m)))
        g = lambda k: (ens[k][i], ens[k + "_se"][i])
        rows.append({"mach_target": float(mt[i]), "l_target": float(lt[i]),
                     **{k: g(k) for k in ("mach_peak_fit", "mach_peak_smooth", "mach_peak_raw", "u_peak_fit",
                                          "rho0_over_rho_inf", "T0_over_T_inf", "kn_local")},
                     "l_fit_over_l_target": (ens["l_fit"][i] / lt[i], (ens["l_fit_se"][i] or 0) / lt[i] if ens["l_fit_se"][i] is not None else None)})
    return rows


def main():
    OUT.mkdir(exist_ok=True)
    files = {Path(f).stem: f for f in glob.glob(str(RUNS / "*.json"))}
    if not files:
        print("no raw runs under", RUNS)
        return 1
    gates, runs_out = {}, {}

    # ---- M1/M2/M3
    gas_eos, liq_names = eos(0.15, 2.0), [k for k in files if k.startswith("gate_liq")]
    eq = [load(files[k]) for k in sorted(files) if k.startswith("gate_gas")]
    if eq:
        p = np.mean([d["p_mean"] for d in eq])
        rho_act = eq[0]["rho"]
        e_act = eos(rho_act, 2.0)
        gates["M1_nve"] = {"dt": eq[0]["dt"], "steps": eq[0]["nve_steps"], "N": eq[0]["N"],
                           "energy_drift_over_KE_per_particle": [d["energy_drift_over_KE"] for d in eq],
                           "momentum_per_particle_max": max(max(abs(x) for x in d["momentum_per_particle"]) for d in eq),
                           "pass": all(d["energy_drift_over_KE"] < 1e-4 for d in eq)}
        gates["M2_equilibrium"] = {
            "rho_actual": rho_act, "T_mean": [d["T_mean"] for d in eq], "p_md": p,
            "p_second_virial": e_act["p_B2"], "p_third_virial": e_act["p_B2_B3"],
            "rel_diff_vs_B2": p / e_act["p_B2"] - 1, "rel_diff_vs_B2_B3": p / e_act["p_B2_B3"] - 1,
            "B2": e_act["B2"], "B3": e_act["B3"], "kurtosis": [d["kurtosis_mean"] for d in eq],
            "pass": all(abs(d["T_mean"] / 2.0 - 1) < 0.01 for d in eq) and abs(p / e_act["p_B2_B3"] - 1) < 0.03
                    and all(abs(d["kurtosis_mean"] / 3 - 1) < 0.02 for d in eq),
            "note": "T is measured in NVE after a Langevin equilibration; pass criterion uses the third-virial EOS "
                    "(B2 alone is off by the size of the B3 term, reported).",
        }
        gates["M3_sound_speed"] = {**{k: e_act[k] for k in ("c_adiabatic", "c_ideal_sqrt_gamma_T", "gamma_eff_c2_over_dpdrhoT", "cv", "Z_B2_B3", "mean_free_path")},
                                   "formula": "c^2 = (dp/drho)_T + T (dp/dT)_rho^2 / (rho^2 c_v), third-order virial EOS of the truncated-shifted potential; "
                                              "local Mach numbers use sqrt(gamma T_loc), gamma = 5/3 (approximate)"}
    if liq_names:
        dl = load(files[sorted(liq_names)[0]])
        gates["liquid_state_point"] = {"rho": dl["rho"], "T_mean": dl["T_mean"], "p_md": dl["p_mean"],
                                       "energy_drift_over_KE": dl["energy_drift_over_KE"], "kurtosis": dl["kurtosis_mean"], "dt": dl["dt"]}

    # ---- M4/M5 from the free-decay runs
    for tag, state in (("decay_gas", "gas"), ("decay_liq", "liquid")):
        dec = [load(files[k]) for k in sorted(files) if k.startswith(tag)]
        if not dec:
            continue
        v = viscosity_from_decay(dec)
        ens = ensemble(dec, KEYS)
        v["T_inner_over_T_inf_min_max"] = [float(np.min(ens["T_inner_mean_over_T_inf"])), float(np.max(ens["T_inner_mean_over_T_inf"]))]
        v["far_swirl_ratio_min_max"] = [float(np.min(ens["far_swirl_over_lamb_oseen"])), float(np.max(ens["far_swirl_over_lamb_oseen"]))]
        v["setup"] = {k: dec[0][k] for k in ("re", "l_start", "R_b", "L", "Lz", "N", "t_run", "dt")}
        v["peak_mach_at_start"] = float(ens["mach_peak_fit"][0])
        if state == "gas":
            v["chapman_enskog_nu"] = gas_eos["nu_chapman_enskog"]
            v["modified_enskog_nu"] = gas_eos["nu_modified_enskog"]
            v["ratio_md_over_modified_enskog"] = v["nu_mean"] / gas_eos["nu_modified_enskog"]
            v["pass_M4"] = abs(v["ratio_md_over_modified_enskog"] - 1) < 0.15
            v["pass_M5"] = abs(v["T_inner_over_T_inf_min_max"][0] - 1) < 0.02 and abs(v["T_inner_over_T_inf_min_max"][1] - 1) < 0.02
        gates[f"M4_M5_{state}"] = v

    # ---- forced runs
    groups = {}
    for k in sorted(files):
        if k.startswith("forced_"):
            groups.setdefault(k.rsplit("_s", 1)[0], []).append(load(files[k]))
    c_inf = gates.get("M3_sound_speed", {}).get("c_adiabatic", np.sqrt(GAMMA * 2.0))
    for name, rs in groups.items():
        ens = ensemble(rs, KEYS)
        d0 = rs[0]
        liquid = d0["rho"] > 0.5
        c_ref = c_inf if not liquid else None
        entry = {"n_seeds": len(rs), "setup": {k: d0[k] for k in ("re", "nu_used", "l_start", "l_end", "R_b", "L", "Lz", "N", "rho", "T_inf", "dt", "Gamma")},
                 "wall_s": [d["wall_s"] for d in rs], "series": ens}
        if not liquid:
            entry["c_inf"] = c_ref
            entry["mach_target"] = (d0["re"] * d0["nu_used"] / np.array(ens["l_target"]) / c_ref).tolist()
            entry["table"] = table(ens, [0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0], c_ref, d0["re"], d0["nu_used"])
        else:
            s = series(rs[0])
            cav = next((i for i, x in enumerate(s["rho0_over_rho_inf"]) if x < 0.5), None)
            entry["cavitation"] = None if cav is None else {
                "t": float(s["t"][cav]), "l_target": float(s["l_target"][cav]), "u_peak_smooth": float(s["u_peak_smooth"][cav]),
                "u_target_peak": float(d0["re"] * d0["nu_used"] / s["l_target"][cav]), "rho0_over_rho_inf": float(s["rho0_over_rho_inf"][cav])}
            entry["u_peak_smooth_max"] = float(np.nanmax(s["u_peak_smooth"]))
            entry["u_target_peak_end"] = float(d0["re"] * d0["nu_used"] / s["l_target"][-1])
            snaps = np.linspace(0, len(rs[0]["windows"]) - 1, 6).astype(int)
            entry["density_snapshots"] = [{"t": rs[0]["windows"][i]["t_mid"], "l_target": rs[0]["windows"][i]["l_target"],
                                           "r": rs[0]["r"][:40].tolist(), "rho": rs[0]["windows"][i]["rho"][:40].tolist()} for i in snaps]
        runs_out[name] = entry
    runs_out["_comparator"] = {
        "gas": {"nu_md": gates.get("M4_M5_gas", {}).get("nu_mean"), "nu_md_se": gates.get("M4_M5_gas", {}).get("nu_se"),
                "c_inf": c_inf, "gamma": GAMMA, "prandtl": 2.0 / 3.0, "viscosity_T_exponent": "not measured; 0.7-0.8 assumed (LJ gas near T* = 2)",
                "rho": 0.15, "T": 2.0, "mean_free_path": gas_eos["mean_free_path"]},
        "note": "match the 1D continuum solver with Re, l_start / (Re nu / c), force per unit mass, monatomic ideal gas",
    }
    runs_out["_estimators"] = __doc__.split("Estimators, and their known biases")[1].strip()

    jd = lambda o: json.dumps(o, indent=1, default=lambda x: x.tolist() if hasattr(x, "tolist") else float(x))
    (OUT / "md_core_gates.json").write_text(jd(gates))
    (OUT / "md_core_runs.json").write_text(jd(runs_out))
    plot(runs_out)
    print(jd({k: {kk: vv for kk, vv in v.items() if kk not in ("per_seed",)} for k, v in gates.items()})[:3000])
    return 0


def plot(runs_out):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # pragma: no cover
        print("plot skipped:", e)
        return
    has_liq = any(not n.startswith("_") and "density_snapshots" in e for n, e in runs_out.items())
    fig, ax = plt.subplots(1, 3 if has_liq else 2, figsize=(16, 4.6) if has_liq else (11.5, 4.6))
    cols = {"forced_gas_re16": "tab:red", "forced_gas_re4": "tab:blue", "forced_gas_re32": "tab:purple"}
    for name, e in runs_out.items():
        if name.startswith("_") or "mach_target" not in e:
            continue
        mt, s, c = np.array(e["mach_target"]), e["series"], cols.get(name, "k")
        m, se = np.array(s["mach_peak_fit"], float), np.array([x or 0 for x in s["mach_peak_fit_se"]], float)
        ax[0].plot(mt, m, color=c, label=f"MD {name} (fit estimator, n={e['n_seeds']})")
        ax[0].fill_between(mt, m - se, m + se, color=c, alpha=0.25)
        ax[0].plot(mt, s["mach_peak_smooth"], color=c, ls=":", lw=0.9, label=f"MD {name} (smoothed-profile max; biased up where bins are sparse)")
        ax[1].plot(mt, s["rho0_over_rho_inf"], color=c, label=f"rho0 {name}")
        ax[1].plot(mt, s["T0_over_T_inf"], color=c, ls="--", label=f"T0 {name}")
    match = OUT / "compressible_core_md_match.json"
    if match.exists():                                          # continuum prediction (1D NSF solver, same set-up)
        cm = json.loads(match.read_text())
        for key, byrun in cm.items():
            if key.startswith("_") or not isinstance(byrun, dict):
                continue
            v = byrun.get("buffer_3.2") or next(iter(byrun.values()))
            c = cols.get(f"forced_gas_{key}", "k")
            if f"forced_gas_{key}" not in runs_out:
                continue                                        # only overlay Reynolds numbers that have MD data
            ax[0].plot(v["mach_target"], v["mach_local"], color=c, ls="--", lw=1.4,
                       label=f"continuum prediction {key} (registered before the MD runs)")
            ax[1].plot(v["mach_target"], v["rho0"], color="k", lw=0.9, label=f"continuum rho0 {key}")
            ax[1].plot(v["mach_target"], v["T0"], color="k", ls="--", lw=0.9, label=f"continuum T0 {key}")
    x = np.array([0.2, 3.5])
    ax[0].plot(x, x, "k:", lw=0.8, label="incompressible target")
    ax[0].set_xlabel("target Mach number  Re nu / (l c)"); ax[0].set_ylabel("peak local Mach number")
    ax[0].set_title("MD forced core: does the Mach number lock?"); ax[0].legend(fontsize=7); ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[1].set_xlabel("target Mach number"); ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_title("core density (solid) and temperature (dashed)"); ax[1].legend(fontsize=6)
    liq = [e for n, e in runs_out.items() if not n.startswith("_") and "density_snapshots" in e]
    if liq:
        for sshot in liq[0]["density_snapshots"]:
            ax[2].plot(sshot["r"], sshot["rho"], label=f"l_target = {sshot['l_target']:.1f}")
        ax[2].set_xlabel("r / sigma"); ax[2].set_ylabel("density"); ax[2].set_title("liquid run: density profiles (exploratory)"); ax[2].legend(fontsize=7)

    for a in ax:
        a.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(OUT / "md_core.png", dpi=130)


if __name__ == "__main__":
    sys.exit(main())
