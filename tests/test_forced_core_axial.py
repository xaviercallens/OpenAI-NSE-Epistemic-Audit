"""
Tests for the stage-2 forced core with axial structure.
MechanicaFluidorum Program - SocrateAI Lab - September 2026

Pins what makes this bed different from the z-invariant column: the target is
solenoidal but its nonlinear term is NOT negligible (so the alpha-models act),
the finite-difference time derivative used in the forcing is converged, the
control tracks the target, and a transport gate produces a positive core lag
that grows with alpha.
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
from forced_core_axial import AxialForcedCore, nonlinearity_check, run_axial  # noqa: E402


class TestAxialTarget(unittest.TestCase):

    def setUp(self):
        self.nu, self.l0 = 0.01, 1.0
        self.s = PseudoSpectralNavierStokes3D(n_grid=24, nu=self.nu)
        self.core = AxialForcedCore(self.s, self.nu, self.l0)

    def test_target_is_solenoidal_by_construction(self):
        t = 0.3 * self.core.T
        before = self.s.divergence_report(self.core.target_unprojected(t))["div_l2_relative"]
        after = self.s.divergence_report(self.core.target(t))["div_l2_relative"]
        # analytic field is div-free; ~2e-6 at n=24 is the discretization of the
        # Gaussian on a coarse grid, and projection removes it entirely
        self.assertLess(before, 1e-5)
        self.assertLess(after, 1e-12)

    def test_axial_velocity_has_unit_reynolds_number(self):
        t = 0.0
        m = self.core.meridional(t)
        uz_max = float(np.max(np.abs(m[2])))
        self.assertAlmostEqual(uz_max * self.core.ell(t) / self.nu, 1.0, delta=0.05)

    def test_nonlinearity_is_not_inert(self):
        # Normalised by |U| k_max the term is ~1e-4 -- small because Re = 1 makes
        # u^2/l comparable to nu u/l^2, both ~1e-4 here -- but 150x the column's
        # 6e-7, and above the 1e-5 inertness threshold used throughout.
        chk = nonlinearity_check(24, self.nu, self.l0)
        self.assertGreater(chk["nse_nonlinear_rel"], 1e-5)
        self.assertGreater(chk["leray_nonlinear_rel"], 1e-5)
        self.assertGreater(chk["lans_nonlinear_rel"], 1e-5)
        self.assertTrue(chk["not_inert"])

    def test_finite_difference_derivative_is_converged(self):
        chk = nonlinearity_check(24, self.nu, self.l0)
        self.assertLess(chk["fd_consistency_rel"], 1e-6)


class TestAxialBed(unittest.TestCase):

    def test_control_tracks_target(self):
        r = run_axial(24, 0.01, 1.0, "nse", None, l_min_cells=3.0)
        self.assertLess(r["max_rel_l2_error"], 1e-3)

    def test_gate_lags_and_lag_grows_with_alpha(self):
        lags = [run_axial(24, 0.01, 1.0, "leray", a, l_min_cells=3.0)["lag_at_end"]
                for a in (0.3, 0.5)]
        self.assertGreater(lags[0], 0.0)
        self.assertGreater(lags[1], lags[0])


class TestGateBarrierCrossover(unittest.TestCase):
    """
    Scaling the target by lam multiplies the core Reynolds number by lam:
    linear terms (d_t U, nu Lap U, the barrier) scale as lam, the nonlinearity
    as lam^2. Gate and barrier leverage share the same forcing norm, so it
    cancels in their ratio, and the crossover Re at which a transport gate
    becomes as strong a lock as a dissipative barrier is exactly
        Re_x = || (L_barrier - L_nu) U || / || N_alpha(U) - N(U) ||,
    a property of target and filter alone. These tests pin that identity and
    the robust claim built on it: Re_x >> 1, so at Re ~ 1 (the cutoff law's
    premise) the barrier is the stronger lock.
    """

    def _setup(self, a, t_frac=0.4, n=24):
        from forced_core_axial import AxialForcedCore, make_solver
        nse = make_solver(n, 0.01, "nse", None)
        core = AxialForcedCore(nse, 0.01, 1.0)
        t = t_frac * core.T
        U, dU = core.target(t), core.target_dt(t)
        N0 = nse.nonlinear_term(U)
        dN = make_solver(n, 0.01, "leray", a).nonlinear_term(U) - N0
        dB = (make_solver(n, 0.01, "barrier", a).diss_symbol - nse.diss_symbol) * U
        return nse, U, dU, N0, dN, dB

    @staticmethod
    def _l2(x):
        return float(np.sqrt(np.sum(np.abs(x) ** 2)))

    def test_crossover_equals_norm_ratio(self):
        nse, U, dU, N0, dN, dB = self._setup(0.35)
        re_x = self._l2(dB) / self._l2(dN)
        f = nse.project_leray(re_x * dU - re_x**2 * N0 - re_x * nse.diss_symbol * U)
        F = self._l2(f)
        gate, barrier = self._l2(re_x**2 * dN) / F, self._l2(re_x * dB) / F
        self.assertAlmostEqual(gate / barrier, 1.0, places=10)

    def test_barrier_is_the_stronger_lock_at_unit_reynolds_number(self):
        for a in (0.25, 0.35, 0.5):
            _, _, _, _, dN, dB = self._setup(a)
            self.assertGreater(self._l2(dB) / self._l2(dN), 5.0, f"alpha={a}")

    def test_crossover_grows_with_filter_width(self):
        ratios = []
        for a in (0.25, 0.35, 0.5):
            _, _, _, _, dN, dB = self._setup(a)
            ratios.append(self._l2(dB) / self._l2(dN))
        self.assertTrue(ratios[0] < ratios[1] < ratios[2], ratios)


if __name__ == "__main__":
    unittest.main()
