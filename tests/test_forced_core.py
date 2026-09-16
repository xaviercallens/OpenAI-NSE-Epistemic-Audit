"""
Tests for the forced-core test bed (Direction 1).
MechanicaFluidorum Program - SocrateAI Lab - September 2026

The bed exists to satisfy the cutoff law's premise (a Re~1 diffusive core) by
construction. These tests pin the properties that make it a valid test bed:
the target really has Re_core = 1 and the diffusive scaling, the forcing is
solenoidal and equals -2 nu Lap U for the pure column, the control run tracks
the target, the core-size estimator is unbiased on the analytic profile, and
the alpha-models are inert on this target (so the bed tests the barrier only).
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

from spectral3d import PseudoSpectralNavierStokes3D  # noqa: E402
from forced_core import ForcedCore, LAMB_OSEEN_PEAK_FACTOR, alpha_models_are_inert, run_core  # noqa: E402


class TestTargetProfile(unittest.TestCase):

    def setUp(self):
        self.nu, self.l0 = 0.01, 1.0
        self.s = PseudoSpectralNavierStokes3D(n_grid=32, nu=self.nu)
        self.core = ForcedCore(self.s, self.nu, self.l0)

    def test_diffusive_scaling(self):
        for t in (0.0, 0.3 * self.core.T, 0.8 * self.core.T):
            tau = self.core.T - t
            self.assertAlmostEqual(self.core.ell(t), np.sqrt(self.nu * tau), places=12)
            self.assertAlmostEqual(self.core.u_peak(t) * self.core.ell(t) / self.nu, 1.0, places=9)

    def test_target_is_solenoidal_and_z_invariant(self):
        U = self.core.target(0.2 * self.core.T)
        self.assertLess(self.s.divergence_report(U)["div_l2_relative"], 1e-12)
        self.assertEqual(float(np.max(np.abs(U[2]))), 0.0)
        self.assertLess(float(np.max(np.abs(U[:, :, :, 1:]))), 1e-12)  # no k_z content

    def test_core_reynolds_number_is_order_one_in_the_box(self):
        """
        The unbounded Lamb-Oseen formula gives Re_core = 1 exactly; in a 2pi box
        the periodic images and the background rotation from mean-vorticity
        removal shift the measured peak velocity by ~10-20% at l = 1. What the
        cutoff law needs is Re_core ~ 1, which is what is asserted.
        """
        U = self.core.target(0.0)
        re_core = self.s.max_velocity(U) * self.core.ell(0.0) / self.nu
        self.assertAlmostEqual(re_core, 1.0, delta=0.25)

    def test_moment_estimator_recovers_ell_on_analytic_target(self):
        for frac in (0.0, 0.5, 0.75):
            t = frac * self.core.T
            U = self.core.target(t)
            self.assertAlmostEqual(self.core.ell_from_moment(U) / self.core.ell(t), 1.0, delta=0.03)

    def test_forcing_is_solenoidal_and_equals_anti_diffusion(self):
        """
        Pure column: N(U) projects to zero, so f = d_t U - nu Lap U. With the
        paper's l^2 = nu tau the Gaussian obeys d_t omega = -(nu/4) Lap omega, so
        f = -(5/4) nu Lap U, i.e. +(5/4) nu k^2 U_hat. (Lamb-Oseen's l^2 = 4 nu tau
        would give -2 nu Lap U; the factor is a convention, the physics is the same.)
        """
        t = 0.3 * self.core.T
        f = self.core.forcing(t)
        self.assertLess(self.s.divergence_report(f)["div_l2_relative"], 1e-10)
        U = self.core.target(t)
        anti = 1.25 * self.nu * self.s.k_sq * U
        # The discretization-level nonlinear residual (~1e-6 of |U| k_max) is not
        # negligible against a forcing that scales with nu = 0.01, so remove it
        # exactly rather than hide it in a loose tolerance.
        expected = anti - self.core.ref.nonlinear(U)
        rel = np.sqrt(np.sum(np.abs(f - expected) ** 2)) / np.sqrt(np.sum(np.abs(anti) ** 2))
        # The box-truncated Gaussian is not its own periodic sum, so the identity
        # d_t omega = -(nu/4) Lap omega holds only up to the edge term ~exp(-pi^2/l^2)
        # (~1e-6 at l^2 = 0.7). Measured 1.6e-6; assert an order of magnitude above.
        self.assertLess(rel, 2e-5)
        # and the residual really is negligible physically:
        n_rel = np.sqrt(np.sum(np.abs(self.core.ref.nonlinear(U)) ** 2)) / np.sqrt(np.sum(np.abs(anti) ** 2))
        self.assertLess(n_rel, 1e-3)


class TestBedBehaviour(unittest.TestCase):

    def test_alpha_models_inert_on_column(self):
        r = alpha_models_are_inert(24, 0.01, 1.0)
        self.assertTrue(r["inert"], r)

    def test_vortex_sign_is_positive_gamma(self):
        """Guards the sign inversion that once made the core estimator read the box."""
        s = PseudoSpectralNavierStokes3D(n_grid=32, nu=0.01)
        core = ForcedCore(s, 0.01, 1.0)
        wz = core.vorticity_z_slice(core.target(0.0))
        self.assertGreater(wz[16, 16], 0.0)
        # the periodized field carries a uniform floor of -Gamma/(4 pi^2); add it back
        peak = wz[16, 16] + core.gamma / (4.0 * np.pi**2)
        self.assertAlmostEqual(peak / core.omega_peak(0.0), 1.0, delta=0.02)

    def test_control_tracks_target(self):
        r = run_core(32, 0.01, 1.0, None, l_min_cells=3.0)
        self.assertLess(r["max_rel_l2_error"], 1e-4)

    def test_barrier_slows_the_collapse_and_bf_grows_as_alpha_over_tau(self):
        """
        Inside a 32^3 window the B/F = 1 crossing is not reached (the O(1)
        prefactor puts it below the resolved window), so the reachable tests are
        (i) the core lags the target when the barrier is on, and (ii) B/F grows
        as alpha'/(nu tau) with unit slope -- the mechanism the arrest law rests on.
        """
        from forced_core import pooled_bf_law
        runs = [run_core(32, 0.01, 1.0, a, l_min_cells=3.0) for a in (0.36, 0.64)]
        self.assertGreater(runs[1]["lag_at_end"], runs[0]["lag_at_end"])
        self.assertGreater(runs[0]["lag_at_end"], 0.05)
        # Two runs in a 3-cell 32^3 window keep B/F below ~0.3, so this is a
        # smoke test of the mechanism's direction, not of the exponent: B/F must
        # grow with alpha'/(nu tau) (positive slope of order one, tight fit). The
        # quantitative slope (0.87 over 1 decade at 32^3; the 96^3 sweep for the
        # record) is a result, not a unit test.
        law = pooled_bf_law(runs, 0.01)
        self.assertGreater(law["slope"], 0.5)
        self.assertLess(law["slope"], 1.5)
        self.assertGreater(law["r_squared"], 0.8)
        self.assertGreater(law["prefactor_C"], 0.02)
        self.assertLess(law["prefactor_C"], 1.0)


if __name__ == "__main__":
    unittest.main()
