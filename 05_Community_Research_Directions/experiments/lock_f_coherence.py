"""
Lock F, coherent version: shear amplification versus thermal decoherence.

DUAL_SCALE_LOCK_PROGRAMME.md, week item 3. The earlier probe in
noise_and_monitor.py seeded a RANDOM-phase shell; the programme argues the
quantity that matters for the construction's pulses is coherence, and that the
criterion is a competition of two rates:

    sigma       amplification rate of a phase-definite packet on a sheared background
    tau_decoh   time for thermal noise to destroy the packet's phase relation

    sigma * tau_decoh >> 1   coherence outlives amplification
    sigma * tau_decoh << 1   noise wins
    ~ 1                      undecided

Both rates are MEASURED here; nothing below is asserted.

Method
------
* Background: 3D Taylor-Green (u0 = 1). It carries strain, so a linear
  perturbation can in principle be amplified.
* Packet: a single Fourier mode k_p (and its conjugate, so the field is real)
  with a definite polarization e (perpendicular to k_p, so solenoidal) and a
  definite phase. Amplitude chosen so the packet carries ~1e-4 of the
  background energy.
* Tracked observable: a(t) = e . u_hat(k_p, t), normalized so a(0) = a0 e^{i phi}.
  This is the packet's complex amplitude at its own wavevector.
* sigma: least-squares slope of log|a(t)| on a noiseless run. Reported with its
  window and R^2. A negative sigma is reported as such -- a Taylor-Green
  background need not amplify a given mode, and the fixed-k_p amplitude also
  loses energy by scattering to k_p +/- (1,1,1). Several orientations are tried,
  including one with vorticity aligned with the extensional strain axis.
* tau_decoh: ensemble of N noise realizations with the SAME packet. Coherent
  energy C(t) = |<a(t)>|^2 (ensemble mean first), total T(t) = <|a(t)|^2>,
  coherent fraction f(t) = C/T. Fit f ~ exp(-t/tau_decoh) on its decaying part;
  bootstrap CI over ensemble members.
* Controls: theta = 0 must give f = 1 identically (asserted); doubling theta
  should shorten tau_decoh (ratio reported).

Caveat kept in view throughout: this packet is a plane wave on a periodic box,
not the construction's localized, shear-amplified pulses. It measures the two
rates in the simplest setting where both are defined.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from spectral3d import PseudoSpectralNavierStokes3D

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)

N_GRID = 32
NU = 5e-3
DT = 0.02
T_END = 1.5
THETA = 2e-5                 # calibrated in noise_and_monitor.py (FDT checks pass there)
N_ENSEMBLE = 8
PACKET_ENERGY_FRACTION = 1e-4

# (label, wavevector, polarization or None for automatic)
ORIENTATIONS: List[Tuple[str, Tuple[int, int, int], Optional[Tuple[float, float, float]]]] = [
    ("generic k=(6,4,2)", (6, 4, 2), None),
    # Taylor-Green at the origin: du_x/dx = +1 (extension), du_y/dy = -1 (compression).
    # k along the compressive axis, polarization along z gives omega = i k x e along x,
    # i.e. vorticity aligned with the extensional strain axis.
    ("strain-aligned k=(0,7,0) e=z", (0, 7, 0), (0.0, 0.0, 1.0)),
    ("k along extension k=(7,0,0) e=z", (7, 0, 0), (0.0, 0.0, 1.0)),
]


# ---------------------------------------------------------------------------
# packet construction and tracking
# ---------------------------------------------------------------------------

def mode_index(k: Sequence[int], n: int) -> Tuple[int, int, int]:
    return tuple(int(ki) % n for ki in k)  # type: ignore[return-value]


def default_polarization(k: Sequence[int]) -> np.ndarray:
    kv = np.asarray(k, dtype=float)
    trial = np.cross(kv, np.array([0.0, 0.0, 1.0]))
    if np.linalg.norm(trial) < 1e-12:
        trial = np.cross(kv, np.array([1.0, 0.0, 0.0]))
    return trial / np.linalg.norm(trial)


def seed_packet(solver: PseudoSpectralNavierStokes3D, u_hat: np.ndarray,
                k_p: Sequence[int], amplitude: float, phase: float,
                polarization: Optional[Sequence[float]] = None
                ) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add  a0 * e * cos(k_p.x + phi)  to the field, in Fourier space, as the pair
    (k_p, -k_p) with conjugate coefficients so the physical field stays real.
    Returns (seeded u_hat, polarization e).
    """
    n = solver.n
    e = default_polarization(k_p) if polarization is None else np.asarray(polarization, float)
    e = e / np.linalg.norm(e)
    if abs(np.dot(e, np.asarray(k_p, float))) > 1e-12:
        raise ValueError("polarization must be perpendicular to k_p")
    c = 0.5 * amplitude * np.exp(1j * phase) * n**3
    out = u_hat.copy()
    ip, im = mode_index(k_p, n), mode_index([-k for k in k_p], n)
    for j in range(3):
        out[j][ip] += c * e[j]
        out[j][im] += np.conj(c) * e[j]
    return solver.project_leray(out), e


def packet_amplitude(solver: PseudoSpectralNavierStokes3D, u_hat: np.ndarray,
                     k_p: Sequence[int], e: np.ndarray) -> complex:
    """a = e . u_hat(k_p), normalized so that the seeded packet gives a0 e^{i phi}."""
    ip = mode_index(k_p, solver.n)
    return complex(sum(e[j] * u_hat[j][ip] for j in range(3)) / (0.5 * solver.n**3))


def mode_energy(solver: PseudoSpectralNavierStokes3D, u_hat: np.ndarray,
                k_p: Sequence[int]) -> float:
    """Energy per unit volume carried by the (k_p, -k_p) pair."""
    ip, im = mode_index(k_p, solver.n), mode_index([-k for k in k_p], solver.n)
    s = sum(abs(u_hat[j][ip]) ** 2 + abs(u_hat[j][im]) ** 2 for j in range(3))
    return 0.5 * float(s) / solver.n**6


def evolve(solver: PseudoSpectralNavierStokes3D, u_hat: np.ndarray, dt: float,
           n_steps: int, theta: float, rng: Optional[np.random.Generator],
           k_p: Sequence[int], e: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fixed-step integration recording a(t) every step. Returns (t, a, final u_hat)."""
    u = u_hat.copy()
    t = np.zeros(n_steps + 1)
    a = np.zeros(n_steps + 1, dtype=complex)
    a[0] = packet_amplitude(solver, u, k_p, e)
    for i in range(1, n_steps + 1):
        u = solver.ifrk4_step(u, dt)
        if theta > 0:
            u = solver.project_leray(u + solver.thermal_noise_increment(dt, theta, rng))
        t[i] = i * dt
        a[i] = packet_amplitude(solver, u, k_p, e)
    return t, a, u


# ---------------------------------------------------------------------------
# fitting helpers
# ---------------------------------------------------------------------------

def fit_growth_rate(t: np.ndarray, a: np.ndarray, t_lo: float, t_hi: float) -> Dict[str, float]:
    """Slope of log|a| vs t on [t_lo, t_hi]. Returns sigma, R^2, window."""
    m = (t >= t_lo) & (t <= t_hi) & (np.abs(a) > 0)
    x, y = t[m], np.log(np.abs(a[m]))
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum(resid**2) / ss_tot if ss_tot > 0 else float("nan")
    return {"sigma": float(slope), "r_squared": float(r2), "window": [float(t_lo), float(t_hi)],
            "n_points": int(m.sum())}


def coherent_fraction(a_members: np.ndarray) -> np.ndarray:
    """a_members: (N, T) complex.  f(t) = |<a>|^2 / <|a|^2>."""
    coherent = np.abs(np.mean(a_members, axis=0)) ** 2
    total = np.mean(np.abs(a_members) ** 2, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(total > 0, coherent / total, np.nan)


def fit_decoherence_time(t: np.ndarray, f: np.ndarray, f_floor: float = 1e-3
                         ) -> Dict[str, float]:
    """Fit f(t) ~ exp(-t/tau) on the decaying part (t > 0, f_floor < f < 1)."""
    m = (t > 0) & np.isfinite(f) & (f > f_floor) & (f < 1.0)
    if m.sum() < 3:
        return {"tau_decoh": float("nan"), "r_squared": float("nan"), "n_points": int(m.sum())}
    x, y = t[m], np.log(f[m])
    slope, intercept = np.polyfit(x, y, 1)
    resid = y - (slope * x + intercept)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - np.sum(resid**2) / ss_tot if ss_tot > 0 else float("nan")
    tau = -1.0 / slope if slope < 0 else float("inf")
    return {"tau_decoh": float(tau), "r_squared": float(r2), "n_points": int(m.sum())}


def bootstrap_tau(t: np.ndarray, a_members: np.ndarray, n_boot: int = 500,
                  seed: int = 0) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    n = a_members.shape[0]
    taus = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(idx)) < 2:
            continue
        tau = fit_decoherence_time(t, coherent_fraction(a_members[idx]))["tau_decoh"]
        if np.isfinite(tau):
            taus.append(tau)
    if not taus:
        return {"ci95": [float("nan"), float("nan")], "n_boot_valid": 0}
    lo, hi = np.percentile(taus, [2.5, 97.5])
    return {"ci95": [float(lo), float(hi)], "n_boot_valid": len(taus)}


# ---------------------------------------------------------------------------
# main experiment
# ---------------------------------------------------------------------------

def run_experiment(verbose: bool = True) -> Dict:
    solver = PseudoSpectralNavierStokes3D(n_grid=N_GRID, nu=NU)
    n_steps = int(round(T_END / DT))
    background = solver.initialize_taylor_green(u0=1.0)
    e_bg = solver.energy(background)
    a0 = np.sqrt(4.0 * PACKET_ENERGY_FRACTION * e_bg)   # packet energy = a0^2/4
    phase = 0.7

    results: Dict = {"config": {"n_grid": N_GRID, "nu": NU, "dt": DT, "t_end": T_END,
                                "theta": THETA, "n_ensemble": N_ENSEMBLE,
                                "packet_energy_fraction": PACKET_ENERGY_FRACTION,
                                "a0": float(a0), "phase": phase},
                     "orientations": []}

    # ---- sigma: noiseless runs, several orientations ---------------------
    t0 = time.time()
    best = None
    for label, k_p, pol in ORIENTATIONS:
        u_seed, e = seed_packet(solver, background, k_p, a0, phase, pol)
        t, a, _ = evolve(solver, u_seed, DT, n_steps, 0.0, None, k_p, e)
        fit_full = fit_growth_rate(t, a, 0.0, T_END)
        fit_late = fit_growth_rate(t, a, 0.2 * T_END, T_END)
        rec = {"label": label, "k_p": list(k_p), "polarization": e.tolist(),
               "abs_k": float(np.linalg.norm(k_p)),
               "viscous_decay_rate_nu_k2": float(NU * np.dot(k_p, k_p)),
               "fit_full_window": fit_full, "fit_late_window": fit_late,
               "log_abs_a": np.log(np.abs(a)).tolist(), "t": t.tolist()}
        results["orientations"].append(rec)
        if verbose:
            print(f"  {label:<36} sigma(full)={fit_full['sigma']:+.3f} R2={fit_full['r_squared']:.3f}"
                  f"   sigma(late)={fit_late['sigma']:+.3f} R2={fit_late['r_squared']:.3f}"
                  f"   nu k^2={NU*np.dot(k_p,k_p):.3f}")
        if best is None or fit_late["sigma"] > best[1]["fit_late_window"]["sigma"]:
            best = (label, rec, k_p, pol)
    results["sigma_timing_s"] = round(time.time() - t0, 1)

    label, rec, k_p, pol = best
    sigma = rec["fit_late_window"]["sigma"]
    results["selected_orientation"] = label
    results["sigma"] = sigma
    results["sigma_fit"] = rec["fit_late_window"]

    # ---- tau_decoh: ensembles on the selected orientation ------------------
    u_seed, e = seed_packet(solver, background, k_p, a0, phase, pol)

    def ensemble(theta: float, n_members: int, seed_base: int) -> Tuple[np.ndarray, np.ndarray]:
        members = []
        tt = None
        for m in range(n_members):
            rng = np.random.default_rng(seed_base + m)
            tt, a, _ = evolve(solver, u_seed, DT, n_steps, theta, rng, k_p, e)
            members.append(a)
        return tt, np.array(members)

    t0 = time.time()
    t, a_theta = ensemble(THETA, N_ENSEMBLE, 100)
    f_theta = coherent_fraction(a_theta)
    fit_theta = fit_decoherence_time(t, f_theta)
    boot_theta = bootstrap_tau(t, a_theta)
    results["ensemble_theta"] = {"theta": THETA, "f": f_theta.tolist(), "t": t.tolist(),
                                 "fit": fit_theta, "bootstrap": boot_theta}

    t2, a_2theta = ensemble(2.0 * THETA, N_ENSEMBLE, 200)
    f_2theta = coherent_fraction(a_2theta)
    fit_2theta = fit_decoherence_time(t2, f_2theta)
    boot_2theta = bootstrap_tau(t2, a_2theta)
    results["ensemble_2theta"] = {"theta": 2.0 * THETA, "f": f_2theta.tolist(),
                                  "fit": fit_2theta, "bootstrap": boot_2theta}
    results["tau_timing_s"] = round(time.time() - t0, 1)

    # ---- control (i): theta = 0 keeps f = 1 exactly -----------------------
    t0c, a_zero = ensemble(0.0, 3, 300)
    f_zero = coherent_fraction(a_zero)
    max_dev = float(np.nanmax(np.abs(f_zero - 1.0)))
    results["control_theta0"] = {"max_abs_deviation_from_1": max_dev, "pass": max_dev < 1e-12}
    assert max_dev < 1e-12, f"theta=0 ensemble should be perfectly coherent; got dev {max_dev}"

    # ---- control (ii): doubling theta -------------------------------------
    tau1, tau2 = fit_theta["tau_decoh"], fit_2theta["tau_decoh"]
    ratio = tau2 / tau1 if (np.isfinite(tau1) and np.isfinite(tau2) and tau1 > 0) else float("nan")
    results["control_double_theta"] = {"tau_theta": tau1, "tau_2theta": tau2,
                                       "ratio_tau2_over_tau1": float(ratio),
                                       "diffusive_expectation": 0.5}

    # ---- thermal floor in the packet's mode (no packet) --------------------
    t0 = time.time()
    rng = np.random.default_rng(999)
    u = np.zeros_like(background)
    n_floor = 600
    e_mode = []
    for i in range(n_floor):
        u = solver.ifrk4_step(u, DT)
        u = solver.project_leray(u + solver.thermal_noise_increment(DT, THETA, rng))
        if i >= n_floor // 2:
            e_mode.append(mode_energy(solver, u, k_p))
    floor = float(np.mean(e_mode))
    packet_e = mode_energy(solver, u_seed, k_p) - mode_energy(solver, background, k_p)
    results["thermal_floor"] = {"mode_energy_floor": floor,
                                "packet_mode_energy_initial": float(packet_e),
                                "packet_over_floor": float(packet_e / floor) if floor > 0 else float("inf"),
                                "timing_s": round(time.time() - t0, 1)}

    # ---- the criterion -----------------------------------------------------
    product = sigma * tau1 if np.isfinite(tau1) else float("nan")
    if not np.isfinite(product):
        verdict = "undetermined (tau_decoh not fitted)"
    elif sigma <= 0:
        verdict = ("no amplification measured (sigma <= 0): the criterion is moot for this "
                   "packet/background -- there is nothing for coherence to protect")
    elif product > 10:
        verdict = "coherence outlives amplification (sigma*tau >> 1)"
    elif product < 0.1:
        verdict = "noise wins (sigma*tau << 1)"
    else:
        verdict = "undecided (sigma*tau ~ 1)"
    results["criterion"] = {"sigma": sigma, "tau_decoh": tau1,
                            "tau_decoh_ci95": boot_theta["ci95"],
                            "sigma_times_tau": float(product), "verdict": verdict}
    return results


def make_figure(res: Dict, path: Path) -> Optional[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for o in res["orientations"]:
        ax[0].plot(o["t"], o["log_abs_a"], label=f"{o['label']}  σ={o['fit_late_window']['sigma']:+.2f}")
    ax[0].set_xlabel("t"); ax[0].set_ylabel("log|a(t)|  (noiseless)")
    ax[0].set_title("Packet amplitude at its own wavevector")
    ax[0].legend(fontsize=7); ax[0].grid(alpha=.3)

    e1, e2 = res["ensemble_theta"], res["ensemble_2theta"]
    t = np.array(e1["t"])
    for e_, c, lab in ((e1, "#1f77b4", "θ"), (e2, "#d62728", "2θ")):
        f = np.array(e_["f"]); tau = e_["fit"]["tau_decoh"]
        ax[1].semilogy(t, f, "o", ms=3, color=c, label=f"{lab}: τ={tau:.2f}")
        if np.isfinite(tau):
            ax[1].semilogy(t, np.exp(-t / tau), "-", color=c, alpha=.7)
    ax[1].set_xlabel("t"); ax[1].set_ylabel("coherent fraction f = |⟨a⟩|²/⟨|a|²⟩")
    ax[1].set_title(f"Decoherence (N={res['config']['n_ensemble']})")
    ax[1].legend(fontsize=8); ax[1].grid(alpha=.3, which="both")
    c = res["criterion"]
    fig.suptitle(f"Lock F: σ={c['sigma']:+.3f}, τ_decoh={c['tau_decoh']:.2f}, "
                 f"σ·τ={c['sigma_times_tau']:+.2f} — {c['verdict']}", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return str(path)


def main() -> None:
    print("=" * 78)
    print(" LOCK F (coherent): shear amplification vs thermal decoherence")
    print("=" * 78)
    print(f" grid {N_GRID}^3  nu={NU}  dt={DT}  t_end={T_END}  theta={THETA}  N={N_ENSEMBLE}\n")
    print("[sigma] noiseless runs:")
    res = run_experiment()
    c = res["criterion"]
    print(f"\n selected orientation: {res['selected_orientation']}")
    print(f" sigma            = {c['sigma']:+.4f}   (R^2={res['sigma_fit']['r_squared']:.3f}, "
          f"window {res['sigma_fit']['window']})")
    print(f" tau_decoh        = {c['tau_decoh']:.4f}   95% CI {c['tau_decoh_ci95']}   "
          f"(R^2={res['ensemble_theta']['fit']['r_squared']:.3f})")
    print(f" sigma * tau      = {c['sigma_times_tau']:+.4f}")
    print(f" verdict          : {c['verdict']}")
    cd = res["control_double_theta"]
    print(f"\n control theta=0  : max|f-1| = {res['control_theta0']['max_abs_deviation_from_1']:.2e} -> "
          f"{'PASS' if res['control_theta0']['pass'] else 'FAIL'}")
    print(f" control 2*theta  : tau(2θ)/tau(θ) = {cd['ratio_tau2_over_tau1']:.3f}   "
          f"(diffusive expectation 0.5)")
    fl = res["thermal_floor"]
    print(f" thermal floor    : mode energy {fl['mode_energy_floor']:.3e}; packet/floor = "
          f"{fl['packet_over_floor']:.2f}")

    # Figure first: the slimming below mutates the shared orientation records.
    fig = make_figure(res, OUT / "lock_f_coherence.png")
    slim = {k: v for k, v in res.items()}
    for o in slim["orientations"]:
        o.pop("log_abs_a", None); o.pop("t", None)
    path = OUT / "lock_f_coherence.json"
    path.write_text(json.dumps(slim, indent=2))
    print(f"\n written to {path}" + (f"\n figure: {fig}" if fig else ""))


if __name__ == "__main__":
    main()
