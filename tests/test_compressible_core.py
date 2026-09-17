"""Tests for the 1D compressible Navier-Stokes-Fourier forced core (experiments/compressible_core.py)."""
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import integrate, optimize

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "05_Community_Research_Directions" / "experiments"))
from compressible_core import Config, Core, HOLE_K, PEAK, first_crossing  # noqa: E402

FAST = dict(n=160, l_start=10.0, l_end=1.0, r_max=12.0)


def test_lamb_oseen_constants():
    res = optimize.minimize_scalar(lambda x: -(-np.expm1(-x * x)) / x, bounds=(0.5, 2.0), method="bounded")
    assert abs(-res.fun - PEAK) < 1e-9
    integral, _ = integrate.quad(lambda x: (-np.expm1(-x * x)) ** 2 / x ** 3, 0, np.inf)
    assert abs(integral - np.log(2.0)) < 1e-10          # exact: the hole coefficient is ln2 / PEAK^2
    assert abs(HOLE_K - np.log(2.0) / PEAK ** 2) < 1e-12
    assert abs((np.log(1.25) / HOLE_K) ** -0.5 - 2.762) < 5e-3   # quasi-steady prediction l_c / (Re l*)


def test_rhs_reproduces_target_tendency_in_incompressible_limit():
    core = Core(Config(mu_law="rho", c_scale=50.0, **FAST))
    n = core.cfg.n
    d = core.rhs(0.0, core.initial()).reshape(n, 4)
    eps = 1e-4
    dU = (core.target_u(eps) - core.target_u(-eps)) / (2 * eps) if False else (core.target_u(eps) - core.target_u(0.0)) / eps
    inner = core.r < 5 * core.ls
    assert np.max(np.abs(d[inner, 2] - dU[inner])) / np.max(np.abs(dU)) < 1e-2
    assert np.max(np.abs(d[:, 1])) < 1e-6      # cyclostrophic balance: no radial acceleration
    assert np.max(np.abs(d[:, 0])) < 1e-12     # and no density tendency


def test_core_size_estimator_ignores_far_field_noise():
    core = Core(Config(**FAST))
    u = core.target_u(0.0)
    assert abs(core.core_size(u) / core.ell(0.0) - 1.0) < 2e-3
    noisy = u + 1e-7 * np.sin(core.r) / (1 + core.r)
    assert abs(core.core_size(noisy) / core.ell(0.0) - 1.0) < 2e-3


def test_low_mach_control_tracks_target():
    rec, status = Core(Config(mu_law="rho", c_scale=50.0, **FAST)).run(n_samples=30, verbose=False)
    assert status == "reached_l_end"
    assert max(abs(r["lag"]) for r in rec) < 2e-3
    assert abs(rec[-1]["u_max"] / rec[-1]["u_target_max"] - 1.0) < 2e-3


@pytest.mark.parametrize("force,sign", [("mass", +1), ("volume", -1)])
def test_force_convention_decides_the_sign_of_the_density_feedback(force, sign):
    """mu independent of rho: a per-mass force lags the target, a per-volume force does not."""
    cfg = Config(mu_law="const", force=force, n=200, l_start=12.0, l_end=0.6, r_max=12.0)
    rec, _ = Core(cfg).run(n_samples=40, verbose=False)
    lag = rec[-1]["lag"]
    assert rec[-1]["rho0"] < 0.8                       # a real density hole has formed
    assert lag > 0.05 if sign > 0 else lag < 0.02


def test_constant_nu_compressible_core_runs_ahead_like_the_bgk_gas():
    cfg = Config(mu_law="rho", n=200, l_start=12.0, l_end=0.6, r_max=12.0)
    rec, _ = Core(cfg).run(n_samples=40, verbose=False)
    assert rec[-1]["lag"] < 0.0
    assert rec[-1]["mass_inner"] == pytest.approx(rec[0]["mass_inner"], rel=1e-3)


def test_first_crossing_interpolates():
    rec = [{"lag": 0.0, "l_target": 4.0}, {"lag": 0.2, "l_target": 1.0}]
    assert first_crossing(rec, "lag", 0.1) == pytest.approx(2.0)
    assert first_crossing(rec, "lag", 0.5) is None
