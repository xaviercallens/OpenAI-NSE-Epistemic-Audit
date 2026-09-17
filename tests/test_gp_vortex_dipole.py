"""Tests for the 2D Gross-Pitaevskii vortex-dipole experiment (experiments/gp_vortex_dipole.py).

Units: hbar = m = g = rho_inf = 1, so c = 1, xi = 1/sqrt(2), kappa = 2 pi.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "05_Community_Research_Directions" / "experiments"))
import gp_vortex_dipole as G  # noqa: E402


def test_bogoliubov_dispersion_within_one_percent():
    for r in G.bogoliubov_check(kxi_values=(0.5, 1.0, 2.0)):
        assert r["rel_err"] < 1e-2, r


def test_initial_state_has_four_vortices_with_zero_net_charge_and_periodic_phase():
    d = 8 * G.XI
    Lx, Ly = G.default_box(d)
    g = G.GP2D(Lx, Ly, 0.35 * G.XI, None)
    psi, _ = G.initial_dipoles(g, d)
    vs = G.find_vortices(g, psi)
    assert len(vs) == 4
    assert sum(q for _, _, q in vs) == 0
    # phase continuity across the periodic boundaries is no worse than across interior cells
    step_bx = np.abs(np.angle(psi[:, 0] * np.conj(psi[:, -1]))).max()
    step_ix = np.abs(np.angle(psi[:, 1] * np.conj(psi[:, 0]))).max()
    step_by = np.abs(np.angle(psi[0, :] * np.conj(psi[-1, :]))).max()
    step_iy = np.abs(np.angle(psi[1, :] * np.conj(psi[0, :]))).max()
    assert step_bx < 1.5 * step_ix + 1e-3 and step_by < 1.5 * step_iy + 1e-3


def test_norm_and_energy_conservation():
    d = 6 * G.XI
    Lx, Ly = G.default_box(d)
    g = G.GP2D(Lx, Ly, 0.35 * G.XI, None)
    psi, ph = G.initial_dipoles(g, d)
    psi = g.relax(psi, ph, 100)
    E0, N0 = g.energy(psi), g.norm(psi)
    psi = g.evolve(psi, int(5.0 / g.dt))
    assert abs(g.norm(psi) - N0) / N0 < 1e-12
    assert abs(g.energy(psi) - E0) / E0 < 1e-5


def test_classical_periodic_speed_tends_to_free_law_in_large_box():
    d = 5 * G.XI
    assert abs(G.classical_periodic_U(d, 400 * d, 200 * d) * d - 1.0) < 1e-3


def test_large_separation_pair_moves_at_classical_speed():
    # d = 10 xi: measured U within 3% of the point-vortex speed at the measured separation (periodic lattice)
    r = G.run_dipole(10.0, t_run=20.0, relax_steps=150, verbose=False)
    assert not r["annihilated"]
    assert abs(r["U_over_classical_periodic_at_measured_sep"] - 1.0) < 0.03
    assert r["U"] < 1.0


def test_small_separation_never_exceeds_sound_speed():
    # d = 1.5 xi: the classical law gives 1/d = 0.94 c; the GP state annihilates into a pulse slower than c
    r = G.run_dipole(1.5, t_run=12.0, relax_steps=100, verbose=False)
    speed = r["U"] if r.get("U") is not None else r["pulse_speed_over_c"]
    assert speed < 1.0
