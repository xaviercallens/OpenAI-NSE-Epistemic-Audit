"""
Tests for the 3D pseudo-spectral Navier-Stokes solver.
MechanicaFluidorum Program - SocrateAI Lab - September 2026

Validates:
- Leray projection actually produces a solenoidal field, and the divergence
  floor is float64 for a generic field (guarding the 1e-32 artifact).
- Taylor-Green invariants are exact.
- Energy decays monotonically and the energy balance dE/dt = -eps holds.
- The integrating-factor step reproduces plain RK4 in a non-stiff regime.
- The barrier dissipation operator has the documented form and engages at
  k_alpha = 1/sqrt(alpha') rather than everywhere.
- The validity monitor fires on, and only on, genuine threshold crossings.
- The cutoff law is self-consistent given its premise (guards against the
  analysis silently changing the predicted exponents).
"""

import os
import sys
import unittest

import numpy as np

EXPERIMENTS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '05_Community_Research_Directions', 'experiments')
)
if EXPERIMENTS_DIR not in sys.path:
    sys.path.insert(0, EXPERIMENTS_DIR)

from spectral3d import (  # noqa: E402
    AIR_300K, WATER_300K, PseudoSpectralNavierStokes3D, ValidityMonitor,
    admissible_vorticity_bound,
)


class TestProjectionAndInvariants(unittest.TestCase):

    def test_leray_projection_is_solenoidal(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        rng = np.random.default_rng(0)
        shape = (3,) + s.k_sq.shape
        u = rng.normal(size=shape) + 1j * rng.normal(size=shape)
        p = s.project_leray(u)
        self.assertLess(s.divergence_report(p)["div_l2_relative"], 1e-12)

    def test_projection_is_idempotent(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u = s.initialize_random_solenoidal(seed=2)
        once, twice = s.project_leray(u), s.project_leray(s.project_leray(u))
        rel = float(np.max(np.abs(once - twice)) / np.max(np.abs(once)))
        self.assertLess(rel, 1e-12)

    def test_divergence_floor_is_float64_for_generic_field(self):
        """
        Guards the artifact: Taylor-Green can give ~1e-32 because its few nonzero
        modes have power-of-two coefficients, but a generic field must land at
        ordinary float64 round-off. A method claiming 1e-32 generally is wrong.
        """
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        generic = s.divergence_report(s.initialize_random_solenoidal(seed=5))["div_l2_relative"]
        self.assertGreater(generic, 1e-20, "suspiciously small: check for a special field")
        self.assertLess(generic, 1e-12)

    def test_taylor_green_invariants_exact(self):
        s = PseudoSpectralNavierStokes3D(n_grid=32, nu=1e-2)
        u = s.initialize_taylor_green()
        self.assertAlmostEqual(s.energy(u), 0.125, places=12)
        self.assertAlmostEqual(s.enstrophy(u), 0.375, places=12)

    def test_vortex_tube_initial_condition_is_solenoidal(self):
        s = PseudoSpectralNavierStokes3D(n_grid=32, nu=1e-2)
        u = s.initialize_colliding_vortex_tubes()
        self.assertLess(s.divergence_report(u)["div_l2_relative"], 1e-12)


class TestDynamics(unittest.TestCase):

    def test_energy_decays_and_balances(self):
        # Explicit dt so the number of diagnostic samples is deterministic; with
        # an adaptive CFL step this run produces only three, and the interior
        # trim below would then be empty.
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=2e-2)
        r = s.run(s.initialize_taylor_green(), t_end=0.5, dt=5e-3, diagnostics_every=1)
        self.assertGreater(len(r["t"]), 20)
        self.assertTrue(np.all(np.diff(r["energy"]) <= 1e-14))
        self.assertTrue(np.all(np.diff(r["t"]) > 0), "time series must be strictly increasing")
        dEdt = np.gradient(r["energy"], r["t"])
        mid = slice(2, -2)
        rel = np.max(np.abs(dEdt[mid] + r["dissipation"][mid])) / np.max(r["dissipation"][mid])
        self.assertLess(rel, 5e-3)

    def test_run_metadata_does_not_clobber_the_dissipation_series(self):
        """The operator name must not overwrite the dissipation-rate time series."""
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=2e-2)
        r = s.run(s.initialize_taylor_green(), t_end=0.2, diagnostics_every=2)
        self.assertIsInstance(r["dissipation"], np.ndarray)
        self.assertEqual(r["dissipation_operator"], "laplacian")

    def test_ifrk4_matches_plain_rk4_when_not_stiff(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u0 = s.initialize_random_solenoidal(seed=3, energy=0.1)
        a, b, t, dt = u0.copy(), u0.copy(), 0.0, 1e-3
        for _ in range(20):
            a = s.ifrk4_step(a, dt)
            k1 = s.rhs(t, b)
            k2 = s.rhs(t + dt / 2, b + dt / 2 * k1)
            k3 = s.rhs(t + dt / 2, b + dt / 2 * k2)
            k4 = s.rhs(t + dt, b + dt * k3)
            b = s.project_leray(b + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4))
            t += dt
        rel = np.sqrt(np.sum(np.abs(a - b) ** 2)) / np.sqrt(np.sum(np.abs(a) ** 2))
        self.assertLess(rel, 1e-8)


class TestBarrierOperator(unittest.TestCase):

    def test_barrier_leaves_large_scales_untouched(self):
        """max(1, alpha' k^2) must equal the plain Laplacian below k_alpha."""
        alpha = 1e-2
        plain = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3)
        barrier = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3, alpha_prime=alpha,
                                               dissipation="barrier")
        below = barrier.k_sq < (1.0 / alpha)
        self.assertTrue(np.allclose(barrier.diss_symbol[below], plain.diss_symbol[below]))
        above = barrier.k_sq > (2.0 / alpha)
        self.assertTrue(np.all(np.abs(barrier.diss_symbol[above])
                               > np.abs(plain.diss_symbol[above])))

    def test_bihyper_differs_from_barrier(self):
        """The two operators are distinct; conflating them was a prior error."""
        a = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3, alpha_prime=1e-2,
                                         dissipation="barrier")
        b = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3, alpha_prime=1e-2,
                                         dissipation="bihyper")
        self.assertFalse(np.allclose(a.diss_symbol, b.diss_symbol))

    def test_barrier_wavenumber_and_resolution_flag(self):
        s = PseudoSpectralNavierStokes3D(n_grid=64, nu=1e-3, alpha_prime=1e-2,
                                         dissipation="barrier")
        self.assertAlmostEqual(s.barrier_wavenumber, 10.0, places=9)
        self.assertTrue(s.barrier_is_resolved())
        far = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3, alpha_prime=1e-8,
                                           dissipation="barrier")
        self.assertFalse(far.barrier_is_resolved())

    def test_alpha_prime_required_for_barrier(self):
        with self.assertRaises(ValueError):
            PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-3, dissipation="barrier")


class TestValidityMonitor(unittest.TestCase):

    def test_admissible_bound_values(self):
        self.assertAlmostEqual(
            admissible_vorticity_bound(WATER_300K["nu"], WATER_300K["c_s"]) / 2.25e12, 1.0, places=2)
        self.assertAlmostEqual(
            admissible_vorticity_bound(AIR_300K["nu"], AIR_300K["c_s"]) / 7.54e9, 1.0, places=2)

    def test_monitor_silent_inside_the_regime(self):
        m = ValidityMonitor(nu=WATER_300K["nu"], c_s=WATER_300K["c_s"],
                            lambda_mol=WATER_300K["lambda_mol"], u_scale=1.0, l_scale=1e-2)
        flags = m.update(0.0, u_max_sim=1.0, omega_max_sim=1.0, l_min_sim=0.1)
        self.assertEqual(flags, {})
        self.assertTrue(m.report()["stayed_admissible"])

    def test_monitor_fires_on_mach_crossing(self):
        m = ValidityMonitor(nu=WATER_300K["nu"], c_s=WATER_300K["c_s"],
                            lambda_mol=WATER_300K["lambda_mol"], u_scale=1000.0, l_scale=1e-2)
        flags = m.update(1.0, u_max_sim=1.0, omega_max_sim=1.0, l_min_sim=0.1)
        self.assertIn("mach", flags)
        self.assertEqual(m.report()["first_Ma_crossing_t"], 1.0)

    def test_monitor_fires_on_vorticity_bound(self):
        m = ValidityMonitor(nu=WATER_300K["nu"], c_s=WATER_300K["c_s"],
                            lambda_mol=WATER_300K["lambda_mol"],
                            u_scale=1.0, l_scale=1e-12)
        flags = m.update(2.0, u_max_sim=1.0, omega_max_sim=1e3, l_min_sim=1.0)
        self.assertIn("vorticity", flags)
        self.assertFalse(m.report()["stayed_admissible"])


class TestThermalNoise(unittest.TestCase):

    def test_noise_increment_is_solenoidal_and_scales_with_dt(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        rng = np.random.default_rng(0)
        inc = s.thermal_noise_increment(1e-3, 1e-4, rng)
        self.assertLess(s.divergence_report(inc)["div_l2_relative"], 1e-12)
        # variance proportional to dt: compare ensemble magnitudes at 1x and 4x dt
        def rms(dt, seed):
            r = np.random.default_rng(seed)
            return np.sqrt(np.mean([np.sum(np.abs(s.thermal_noise_increment(dt, 1e-4, r)) ** 2)
                                    for _ in range(8)]))
        self.assertAlmostEqual(rms(4e-3, 1) / rms(1e-3, 1), 2.0, delta=0.25)

    def test_zero_temperature_gives_no_noise(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        rng = np.random.default_rng(0)
        inc = s.thermal_noise_increment(1e-3, 0.0, rng)
        self.assertEqual(float(np.max(np.abs(inc))), 0.0)


class TestCutoffLawSelfConsistency(unittest.TestCase):
    """
    The experimental result is a statement about the law's *premise*, which only
    makes sense if the law itself is arithmetically exact given that premise.
    These guard that reasoning from silently changing.
    """

    def test_law_exponents_are_identities_given_the_premise(self):
        from analyse_cutoff_law import analytic_self_consistency
        a = analytic_self_consistency()
        self.assertTrue(a["Re_core_is_unity"])
        self.assertTrue(a["self_consistent"])
        for key, expected in a["predicted_exponents"].items():
            self.assertAlmostEqual(a["fitted_exponents"][key], expected, places=8)

    def test_resolution_requirement_matches_documented_values(self):
        from analyse_cutoff_law import resolution_requirement
        r = resolution_requirement(omega0=2.0)["by_reynolds"]
        self.assertAlmostEqual(r["400"]["n_required"], 84.85, places=1)
        self.assertAlmostEqual(r["1600"]["n_required"], 169.7, places=1)


if __name__ == "__main__":
    unittest.main()
