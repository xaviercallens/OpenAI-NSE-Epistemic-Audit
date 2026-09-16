"""
Research directions 3 and 4.

(3) Landau-Lifshitz thermal noise, with a fluctuation-dissipation check.

    The paper's Q2 asks whether the exponentially small pulses that seed the
    OpenAI construction survive thermal fluctuations. Before that question can
    be asked of a simulation, the noise implementation has to be *calibrated*,
    not assumed: a stochastic forcing with the wrong prefactor will happily
    produce plausible-looking turbulence that is thermodynamically meaningless.

    The calibration used here is equipartition. For incompressible fluctuating
    hydrodynamics at equilibrium (no mean flow, no forcing), each solenoidal
    degree of freedom should carry the same mean energy, independent of k --
    a flat energy spectrum per mode, and a total energy that is linear in the
    temperature parameter. FDT1/FDT2 below check exactly that, and they are
    checks that can fail.

(4) The runtime model-validity monitor.

    Instruments a run with the paper's local admissibility bound
    |omega| <~ c_s^2/nu (equivalently Ma <~ 1 and Kn <~ 1) and reports when, and
    by how much, the simulated flow leaves the regime in which incompressible
    Navier-Stokes is a valid model *of a real fluid*. This is deliberately not a
    numerical stability check: a run can be perfectly stable and still describe a
    state no fluid can be in.

Usage:  python3 noise_and_monitor.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from spectral3d import (AIR_300K, WATER_300K, PseudoSpectralNavierStokes3D,
                        ValidityMonitor, admissible_vorticity_bound)

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# (3) thermal noise
# ---------------------------------------------------------------------------

def fdt_equilibrium(n: int = 16, nu: float = 0.05, theta: float = 1e-4,
                    t_end: float = 6.0, dt: float = 2e-3, seed: int = 0) -> dict:
    """
    Run noise + viscosity with no initial flow and no forcing, to equilibrium.

    Returns the measured per-mode energy spectrum and its flatness. Equipartition
    predicts E(k)/N_modes(k) independent of k.
    """
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    rng = np.random.default_rng(seed)
    u_hat = np.zeros((3,) + s.k_sq.shape, dtype=np.complex128)

    n_steps = int(t_end / dt)
    burn = n_steps // 2
    acc = np.zeros_like(s.k_sq)
    n_acc = 0
    energies = []
    for i in range(n_steps):
        u_hat = s.ifrk4_step(u_hat, dt)
        u_hat = s.project_leray(u_hat + s.thermal_noise_increment(dt, theta, rng))
        if i >= burn and i % 10 == 0:
            acc += np.sum(np.abs(u_hat) ** 2, axis=0) / (s.n ** 6)
            n_acc += 1
            energies.append(s.energy(u_hat))

    acc /= max(n_acc, 1)
    kbin = np.rint(s.k_mag).astype(int)
    nk = s.n // 2
    e_shell = np.bincount(kbin.ravel(), weights=acc.ravel(), minlength=nk + 1)[: nk + 1]
    counts = np.bincount(kbin.ravel(), minlength=nk + 1)[: nk + 1].astype(float)
    # only shells inside the dealiased band carry meaningful statistics
    kmax = int(s.k_max_effective)
    band = slice(1, max(2, kmax - 1))
    per_mode = np.divide(e_shell, counts, out=np.zeros_like(e_shell), where=counts > 0)
    vals = per_mode[band]
    vals = vals[vals > 0]
    flatness = float(np.std(vals) / np.mean(vals)) if len(vals) else float("nan")
    return {
        "k": list(range(nk + 1)),
        "per_mode_energy": per_mode.tolist(),
        "relative_spread_in_band": flatness,
        "mean_energy": float(np.mean(energies)) if energies else float("nan"),
        "theta": theta,
        "equipartition_ok": bool(flatness < 0.25),
        "note": ("Equipartition predicts per-mode energy independent of k. "
                 "Spread is measured over the dealiased band only."),
    }


def fdt_temperature_linearity(thetas=(2.5e-5, 5e-5, 1e-4, 2e-4)) -> dict:
    """Equilibrium energy must be linear in the temperature parameter."""
    res = []
    for th in thetas:
        r = fdt_equilibrium(n=16, nu=0.05, theta=th, t_end=4.0, seed=1)
        res.append({"theta": th, "mean_energy": r["mean_energy"]})
    x = np.array([r["theta"] for r in res])
    y = np.array([r["mean_energy"] for r in res])
    slope = float(np.polyfit(np.log(x), np.log(y), 1)[0])
    return {
        "samples": res,
        "log_log_slope": slope,
        "expected_slope": 1.0,
        "linear_in_temperature": bool(abs(slope - 1.0) < 0.15),
    }


def pulse_survival(n: int = 32, nu: float = 5e-3, theta: float = 2e-5,
                   pulse_k: int = 8, pulse_amp: float = 1e-3,
                   t_end: float = 2.0, seed: int = 2) -> dict:
    """
    A first, deliberately modest, probe of Q2.

    Seed a small-amplitude high-wavenumber pulse on a background shear, run with
    and without thermal noise, and compare the pulse's energy at the end. This
    does NOT reproduce the OpenAI construction's pulses (which are phase-coherent
    and shear-amplified in a specific arrangement); it measures only whether a
    perturbation of this amplitude at this scale is above or below the thermal
    noise floor.
    """
    out = {}
    for label, th in (("noiseless", 0.0), ("thermal", theta)):
        s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
        u_hat = s.initialize_taylor_green(u0=1.0)
        shell = (np.rint(s.k_mag).astype(int) == pulse_k)
        rng = np.random.default_rng(seed)
        pulse = np.zeros_like(u_hat)
        ph = rng.normal(size=(3,) + s.k_sq.shape) + 1j * rng.normal(size=(3,) + s.k_sq.shape)
        pulse = s.project_leray(ph * shell)
        e_p = s.energy(pulse)
        if e_p > 0:
            pulse *= pulse_amp / np.sqrt(e_p)
        u_hat = s.project_leray(u_hat + pulse)
        e0 = float(np.sum(np.abs(u_hat * shell) ** 2) / (s.n ** 6) / 2.0)
        r = s.run(u_hat, t_end=t_end, cfl=0.4, diagnostics_every=20,
                  temperature_param=th, rng=np.random.default_rng(seed + 1))
        uf = r["u_hat_final"]
        e1 = float(np.sum(np.abs(uf * shell) ** 2) / (s.n ** 6) / 2.0)
        out[label] = {"shell_energy_initial": e0, "shell_energy_final": e1}

    # the thermal floor in that shell, from an equilibrium run with no pulse
    s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu)
    shell = (np.rint(s.k_mag).astype(int) == pulse_k)
    rng = np.random.default_rng(seed + 5)
    u_hat = np.zeros((3,) + s.k_sq.shape, dtype=np.complex128)
    for _ in range(400):
        u_hat = s.ifrk4_step(u_hat, 2e-3)
        u_hat = s.project_leray(u_hat + s.thermal_noise_increment(2e-3, theta, rng))
    floor = float(np.sum(np.abs(u_hat * shell) ** 2) / (s.n ** 6) / 2.0)
    out["thermal_floor_in_shell"] = floor
    out["pulse_above_floor"] = bool(out["noiseless"]["shell_energy_final"] > floor)
    out["caveat"] = (
        "Not the OpenAI pulses: those are phase-coherent and shear-amplified by a "
        "specific construction. This measures only whether a perturbation of this "
        "amplitude and scale sits above the thermal floor."
    )
    return out


# ---------------------------------------------------------------------------
# (4) validity monitor
# ---------------------------------------------------------------------------

def monitor_demo() -> dict:
    """
    Run a decaying TGV twice, mapped onto real water at two different physical
    scales, and report when each leaves the admissible regime.

    The simulation is identical in both cases; only the physical interpretation
    (what one simulation length/velocity unit means in SI) differs. That is the
    point: model validity is not a property of the numerics.
    """
    results = {}
    for label, (u_scale, l_scale) in {
        "laboratory_cm_scale": (1.0, 1e-2),        # 1 m/s over 1 cm
        "extreme_microscale": (300.0, 1e-8),       # 300 m/s over 10 nm
    }.items():
        s = PseudoSpectralNavierStokes3D(n_grid=32, nu=2.5e-3)
        mon = ValidityMonitor(
            nu=WATER_300K["nu"], c_s=WATER_300K["c_s"],
            lambda_mol=WATER_300K["lambda_mol"],
            u_scale=u_scale, l_scale=l_scale,
        )
        r = s.run(s.initialize_taylor_green(), t_end=3.0, cfl=0.4,
                  diagnostics_every=4, monitor=mon)
        rep = r["validity"]
        rep["u_scale_m_per_s"] = u_scale
        rep["l_scale_m"] = l_scale
        results[label] = rep
    results["reference_bounds"] = {
        "water_omega_max_per_s": admissible_vorticity_bound(WATER_300K["nu"], WATER_300K["c_s"]),
        "air_omega_max_per_s": admissible_vorticity_bound(AIR_300K["nu"], AIR_300K["c_s"]),
    }
    return results


def main() -> None:
    print("=" * 78)
    print(" RESEARCH DIRECTIONS 3 (thermal noise) AND 4 (validity monitor)")
    print("=" * 78)

    print("\n[3] Fluctuation-dissipation calibration")
    fdt1 = fdt_equilibrium()
    print(f"  FDT1 equipartition: per-mode energy spread across the band = "
          f"{fdt1['relative_spread_in_band']:.3f}  -> {'PASS' if fdt1['equipartition_ok'] else 'FAIL'}")
    fdt2 = fdt_temperature_linearity()
    print(f"  FDT2 energy vs temperature: log-log slope = {fdt2['log_log_slope']:.3f} "
          f"(expect 1.00)  -> {'PASS' if fdt2['linear_in_temperature'] else 'FAIL'}")

    print("\n[3] Pulse survival probe (Q2, modest version)")
    ps = pulse_survival()
    print(f"  seeded pulse, final shell energy (noiseless): {ps['noiseless']['shell_energy_final']:.3e}")
    print(f"  same with thermal noise:                      {ps['thermal']['shell_energy_final']:.3e}")
    print(f"  thermal floor in that shell:                  {ps['thermal_floor_in_shell']:.3e}")
    print(f"  pulse above the thermal floor: {ps['pulse_above_floor']}")

    print("\n[4] Runtime model-validity monitor")
    mon = monitor_demo()
    print(f"  admissible |omega| bound: water {mon['reference_bounds']['water_omega_max_per_s']:.2e} 1/s, "
          f"air {mon['reference_bounds']['air_omega_max_per_s']:.2e} 1/s")
    for label in ("laboratory_cm_scale", "extreme_microscale"):
        r = mon[label]
        print(f"  {label:22s} scales: {r['u_scale_m_per_s']} m/s over {r['l_scale_m']:.0e} m")
        print(f"    worst Ma={r['worst_Ma']:.3e}  worst Kn={r['worst_Kn']:.3e}  "
              f"worst |omega|/bound={r['worst_vorticity_ratio']:.3e}")
        print(f"    stayed admissible: {r['stayed_admissible']}"
              + ("" if r["stayed_admissible"]
                 else f"   (first crossing: Ma@{r['first_Ma_crossing_t']}, "
                      f"Kn@{r['first_Kn_crossing_t']}, |omega|@{r['first_vorticity_crossing_t']})"))

    path = OUT / "noise_and_monitor.json"
    path.write_text(json.dumps(
        {"fdt_equipartition": fdt1, "fdt_temperature_linearity": fdt2,
         "pulse_survival": ps, "validity_monitor": mon}, indent=2))
    print(f"\n written to {path}")


if __name__ == "__main__":
    main()
