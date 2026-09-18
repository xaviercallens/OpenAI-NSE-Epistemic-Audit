"""Fast tests for experiments/analyse_md_core.py on synthetic data (no MD runs needed)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "05_Community_Research_Directions" / "experiments"))
import analyse_md_core as a  # noqa: E402


def synthetic_run(nu=1.7, l0=20.0, gamma=130.0, times=(2.5, 7.5, 12.5, 17.5, 22.5, 27.5, 32.5), noise=0.0, seed=0, rho=0.15, T=2.0):
    rng = np.random.default_rng(seed)
    edges = np.concatenate((np.arange(0, 30, 1.0), np.arange(30, 60, 2.0), np.arange(60, 121, 5.0)))
    r = 0.5 * (edges[1:] + edges[:-1])
    vol = np.pi * (edges[1:] ** 2 - edges[:-1] ** 2) * 8.0
    d = {"mode": "vortex", "bin_edges": edges.tolist(), "Lz": 8.0, "R_b": 90.0, "Gamma": gamma, "rho": rho, "T_inf": T,
         "seed": seed, "r": r, "vol": vol, "windows": []}
    for t in times:
        l = np.sqrt(l0 ** 2 + 4 * nu * t)
        n = rho * vol
        d["windows"].append({"t_mid": t, "l_target": l, "samples": 20, "n_per_sample": n, "rho": np.full_like(r, rho),
                             "u_theta": a.lamb_oseen(r, gamma, l) + noise * rng.standard_normal(r.size) / np.sqrt(20 * n),
                             "u_r": np.zeros_like(r), "T": np.full_like(r, T)})
    return d


def test_virial_integrals_reproduce_hard_spheres_and_tabulated_lj():
    hs = lambda r: np.where(r < 1.0, 1e9, 0.0)
    assert a.b2(1.0, hs, rmax=1.5) == pytest.approx(2 * np.pi / 3, rel=1e-3)
    assert a.b3(1.0, hs, rmax=1.5, n=1500) == pytest.approx(5 * np.pi ** 2 / 18, rel=5e-3)
    full = lambda r: 4 * (r ** -12 - r ** -6)
    assert a.b2(2.0, full, rmax=60, n=200000) / (2 * np.pi / 3) == pytest.approx(-0.6276, abs=2e-3)


def test_lamb_oseen_fit_recovers_size_and_circulation():
    r = np.linspace(0.5, 80, 120)
    u = a.lamb_oseen(r, 100.0, 12.0)
    l, g = a.fit_lamb_oseen(r, u, np.ones_like(r))
    assert l == pytest.approx(12.0, rel=1e-4) and g == pytest.approx(100.0, rel=1e-4)
    l_fixed, _ = a.fit_lamb_oseen(r, u, np.ones_like(r), gamma=100.0)
    assert l_fixed == pytest.approx(12.0, rel=1e-4)


def test_viscosity_from_free_decay_with_thermal_noise():
    runs = [synthetic_run(nu=1.7, noise=1.4, seed=s) for s in range(4)]
    v = a.viscosity_from_decay(runs, skip=1)
    assert v["nu_mean"] == pytest.approx(1.7, rel=0.05)
    assert v["nu_se"] < 0.1


def test_window_metrics_on_a_clean_vortex():
    d = synthetic_run(noise=0.0)
    m = a.window_metrics(d, d["windows"][0])
    l = d["windows"][0]["l_target"]
    assert m["l_fit"] == pytest.approx(l, rel=1e-3)
    u_peak = a.PEAK * d["Gamma"] / (2 * np.pi * l)
    assert m["u_peak_fit"] == pytest.approx(u_peak, rel=1e-3)
    assert m["mach_peak_fit"] == pytest.approx(u_peak / np.sqrt(a.GAMMA * 2.0), rel=1e-3)
    assert m["u_peak_raw"] <= u_peak * 1.0001                      # no noise: the raw maximum cannot exceed the true peak
    assert m["rho0_over_rho_inf"] == pytest.approx(1.0, rel=1e-6)
    assert m["far_swirl_over_lamb_oseen"] == pytest.approx(1.0, rel=1e-3)


def test_raw_peak_is_biased_upward_by_noise_and_fit_is_not():
    raw, fit = [], []
    for s in range(12):
        d = synthetic_run(noise=6.0, seed=s, times=(2.5,))
        m = a.window_metrics(d, d["windows"][0])
        raw.append(m["u_peak_raw"]); fit.append(m["u_peak_fit"])
    true = a.PEAK * 130.0 / (2 * np.pi * np.sqrt(400 + 4 * 1.7 * 2.5))
    assert np.mean(raw) > true * 1.02
    assert abs(np.mean(fit) / true - 1) < 0.03
