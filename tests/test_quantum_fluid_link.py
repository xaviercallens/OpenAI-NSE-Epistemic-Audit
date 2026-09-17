"""Tests for experiments/quantum_fluid_link.py (quantized vortex, Landau criterion, vortex-lattice modular geometry)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "05_Community_Research_Directions" / "experiments"))
import quantum_fluid_link as q  # noqa: E402


@pytest.fixture(scope="module")
def vortex():
    return q.gp_vortex_profile()


def test_gp_vortex_solves_its_ode_and_matches_asymptotes(vortex):
    r = np.linspace(0.05, 30, 3000)
    f, fp = vortex.sol(r)
    fpp = vortex.sol(r, 1)[1]
    residual = fpp + fp / r - f / r ** 2 - 2 * (f ** 2 - 1) * f
    assert np.max(np.abs(residual[r > 0.2])) < 1e-4
    far = r > 15
    assert np.max(np.abs((1 - f[far]) * 4 * r[far] ** 2 - 1)) < 0.05      # f ~ 1 - 1/(4 r^2)
    assert abs(vortex.sol(1e-3)[0] / 1e-3 - 0.8247) < 5e-3                 # f ~ a r, a = 0.8247 (units hbar=m=c=1)


def test_quantum_reynolds_number_is_identically_one_and_sonic_radius_is_sqrt2_xi():
    a = q.part_a()
    assert a["quantum_reynolds_number_min_max"] == pytest.approx([1.0, 1.0], abs=1e-12)
    assert a["sonic_radius_over_xi"] == pytest.approx(np.sqrt(2))
    # the classical twin empties its core too, and the two density deficits agree far away
    assert a["radius_where_density_is_half"]["classical_isothermal_euler"] == pytest.approx(1 / np.sqrt(2 * np.log(2)), rel=1e-3)
    assert a["max_mass_current_rho_u"]["gp"] < 0.5


def test_landau_critical_velocity_from_dispersion_geometry():
    b = q.part_b()
    assert b["bogoliubov_vc_over_c"] == pytest.approx(1.0, abs=1e-9)
    assert b["free_bose_gas_vc_at_smallest_k"] < 1e-5
    assert 55 < b["he4_landau_vc_m_s"] < 60                                  # roton-limited, ~0.24 c
    assert b["he4_landau_vc_m_s"] <= b["he4_delta_over_hbar_k0_m_s"]


def test_vortex_lattice_energy_is_modular_invariant_and_hexagonal_is_lowest():
    for t in (complex(0.13, 0.91), complex(-0.31, 1.37)):
        assert q.F(t + 1) == pytest.approx(q.F(t), rel=1e-12)
        assert q.F(-1 / t) == pytest.approx(q.F(t), rel=1e-12)
    hexa, square = complex(0.5, np.sqrt(3) / 2), complex(0, 1)
    assert -np.log(q.F(hexa)) < -np.log(q.F(square))
    assert q.epstein_unit_area(hexa) < q.epstein_unit_area(square)
    # nearby shapes are higher than the hexagonal point
    for d in (complex(0.03, 0), complex(0, 0.05), complex(-0.02, 0.04)):
        assert -np.log(q.F(hexa + d)) > -np.log(q.F(hexa))


def test_validity_length_floor_is_mass_independent_fraction_of_bohr_radius():
    d = q.part_d()
    vals = [row["nu_m_over_v_u_m"] for row in d["per_fluid"].values()]
    assert max(vals) / min(vals) - 1 < 1e-12
    assert vals[0] == pytest.approx(d["floor_sqrt2_over_4pi_bohr_radius_m"], rel=1e-6)
    assert 5.5e-12 < d["floor_sqrt2_over_4pi_bohr_radius_m"] < 6.5e-12
    assert d["water_lstar_over_floor"] > 50
