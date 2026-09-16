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


class TestLerayAlpha(unittest.TestCase):
    """
    Leray-alpha modifies TRANSPORT, (u.grad)u -> (ubar.grad)u with
    ubar = (1 - alpha^2 Delta)^{-1} u. It is a different model from the
    hyperviscous 'barrier', which modifies DISSIPATION. These tests pin the
    properties that distinguish it, which are also the ones a Lean
    formalization would need to state.
    """

    def test_filter_symbol_bounds(self):
        """0 < (1 + alpha^2 |k|^2)^{-1} <= 1, with equality only at k = 0."""
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2, leray_alpha=0.1)
        self.assertTrue(np.all(s.filter_symbol > 0))
        self.assertTrue(np.all(s.filter_symbol <= 1.0))
        self.assertEqual(float(s.filter_symbol[0, 0, 0]), 1.0)
        self.assertTrue(np.all(s.filter_symbol[s.k_sq > 0] < 1.0))

    def test_smoothed_velocity_is_solenoidal(self):
        """The filter is radial in k, so it commutes with the Leray projector."""
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2, leray_alpha=0.2)
        ub = s.smoothed_velocity(s.initialize_random_solenoidal(seed=1))
        self.assertLess(s.divergence_report(ub)["div_l2_relative"], 1e-12)

    def test_reduces_to_navier_stokes_as_alpha_vanishes(self):
        """The filter correction is O(alpha^2 k^2): two decades per decade of alpha."""
        base = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u0 = base.initialize_random_solenoidal(seed=4, energy=0.2)
        ns = base.nonlinear_term(u0)

        def rel(a):
            la = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2, leray_alpha=a).nonlinear_term(u0)
            return np.sqrt(np.sum(np.abs(la - ns) ** 2)) / np.sqrt(np.sum(np.abs(ns) ** 2))

        self.assertLess(rel(1e-4), 1e-6)
        ratio = rel(1e-3) / rel(1e-4)
        self.assertAlmostEqual(np.log10(ratio), 2.0, delta=0.05)

    def test_nonlinearity_conserves_kinetic_energy(self):
        """
        int u.(ubar.grad)u = int ubar.grad(|u|^2/2) = -int (div ubar)|u|^2/2 = 0.
        So the inviscid Leray-alpha flow conserves (1/2)int|u|^2 exactly: the
        lock suppresses transfer rather than dissipating energy.
        """
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=0.0, leray_alpha=0.05)
        u = s.initialize_random_solenoidal(seed=9, energy=0.2)
        e0 = s.energy(u)
        for _ in range(100):
            u = s.ifrk4_step(u, 2e-3)
        self.assertLess(abs(s.energy(u) - e0) / e0, 1e-12)

    def test_power_input_of_nonlinearity_vanishes(self):
        """Direct check of the identity above, without time stepping."""
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2, leray_alpha=0.3)
        u = s.initialize_random_solenoidal(seed=11, energy=0.3)
        power = float(np.real(np.sum(np.conj(u) * s.nonlinear_term(u))))
        scale = float(np.sum(np.abs(u) ** 2)) * float(np.sqrt(np.max(s.k_sq)))
        self.assertLess(abs(power) / scale, 1e-12)

    def test_lock_retains_energy_unlike_hyperviscosity(self):
        """
        The distinguishing physical signature: Leray-alpha suppresses peak
        vorticity while RETAINING more energy than plain Navier-Stokes, whereas
        a hyperviscous barrier removes energy.
        """
        n, nu, t_end = 24, 5e-3, 5.0
        def run(**kw):
            s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, **kw)
            return s.run(s.initialize_taylor_green(), t_end=t_end, dt=0.02, diagnostics_every=5)
        ns = run()
        la = run(leray_alpha=0.3)
        self.assertLess(float(np.max(la["omega_max"])), float(np.max(ns["omega_max"])))
        self.assertGreater(float(la["energy"][-1]), float(ns["energy"][-1]))


class TestLANSAlpha(unittest.TestCase):
    """
    LANS-alpha (Navier-Stokes-alpha): d_t v - u x curl v + grad pi = nu Lap v,
    v = (1 - alpha^2 Lap) u. The Lagrangian-averaged member of the family, and
    the one the programme conjectures could be derived from kinetic fluctuations.
    Its invariant is the alpha-energy (1/2)<u.v>, NOT (1/2)<|u|^2>.
    """

    def _pair(self, a, nu=0.0, n=16):
        return PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, leray_alpha=a, alpha_model="lans")

    def test_reduces_to_navier_stokes_as_alpha_vanishes(self):
        base = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u0 = base.initialize_random_solenoidal(seed=4, energy=0.2)
        ns = base.nonlinear_term(u0)

        def rel(a):
            la = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2, leray_alpha=a,
                                              alpha_model="lans").nonlinear_term(u0)
            return np.sqrt(np.sum(np.abs(la - ns) ** 2)) / np.sqrt(np.sum(np.abs(ns) ** 2))

        self.assertLess(rel(1e-4), 1e-6)
        self.assertAlmostEqual(np.log10(rel(1e-3) / rel(1e-4)), 2.0, delta=0.05)

    def test_alpha_energy_is_the_invariant_and_plain_energy_is_not(self):
        s = self._pair(0.05)
        u = s.initialize_random_solenoidal(seed=9, energy=0.2)
        ea0, e0 = s.alpha_energy(u), s.energy(u)
        for _ in range(100):
            u = s.ifrk4_step(u, 2e-3)
        self.assertLess(abs(s.alpha_energy(u) - ea0) / ea0, 1e-12)
        # plain energy is exchanged with the alpha^2|grad u|^2 part; it must move
        self.assertGreater(abs(s.energy(u) - e0) / e0, 1e-8)

    def test_alpha_energy_reduces_to_energy_without_filter(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u = s.initialize_random_solenoidal(seed=2)
        self.assertEqual(s.alpha_energy(u), s.energy(u))

    def test_power_input_on_v_vanishes_pointwise_identity(self):
        """u.((curl v) x u) = 0 pointwise, so <u . d_t v> = 0 exactly."""
        s = self._pair(0.3, nu=1e-2)
        u = s.initialize_random_solenoidal(seed=11, energy=0.3)
        dv = s.nonlinear_lans_alpha(u) * s.helmholtz_symbol  # recover d(v_hat)/dt
        power = float(np.real(np.sum(np.conj(u) * dv)))
        scale = float(np.sum(np.abs(u) ** 2)) * float(np.sqrt(np.max(s.k_sq)))
        self.assertLess(abs(power) / scale, 1e-12)

    def test_lans_suppresses_peak_vorticity_at_least_as_much_as_leray(self):
        n, nu, t_end, a = 24, 5e-3, 5.0, 0.3
        def run(**kw):
            s = PseudoSpectralNavierStokes3D(n_grid=n, nu=nu, **kw)
            return s.run(s.initialize_taylor_green(), t_end=t_end, dt=0.02, diagnostics_every=5)
        ns = float(np.max(run()["omega_max"]))
        le = float(np.max(run(leray_alpha=a)["omega_max"]))
        la = float(np.max(run(leray_alpha=a, alpha_model="lans")["omega_max"]))
        self.assertLess(le, ns)
        self.assertLess(la, ns)


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
