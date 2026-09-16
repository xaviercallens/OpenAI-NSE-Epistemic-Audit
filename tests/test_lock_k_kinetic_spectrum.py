"""
Tests for the Lock K kinetic shear-mode spectrum (linearized BGK).
MechanicaFluidorum Program - SocrateAI Lab - September 2026

Pins the facts the programme's "which lock acts at l*" claim now rests on:
the plasma-dispersion evaluation is correct; the kinetic shear mode reduces to
Navier-Stokes at small k; its Burnett-order correction REDUCES damping; two
independent methods agree; the mode's damping never exceeds the collision rate
and it terminates exactly at k lambda = sqrt(pi/2); and the discrete-velocity
BGK operator is stable (the spectral twin of LatticeBGKEntropy.lean).
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

from lock_k_kinetic_spectrum import (  # noqa: E402
    Q_CRIT_ANALYTIC, critical_q_M1, gamma_nse, hydrodynamic_eig_M2, hydrodynamic_root_M1,
    mean_resolvent_quad, mean_resolvent_Z, shear_operator,
)


class TestLockKSpectrum(unittest.TestCase):

    def test_z_identity_matches_quadrature(self):
        for sig, k in ((1.0, 0.1), (0.3, 1.0), (1.2, 3.0), (0.05, 0.7)):
            a, b = mean_resolvent_Z(sig, k), mean_resolvent_quad(sig, k)
            self.assertLess(abs(a - b) / abs(b), 1e-8, (sig, k))

    def test_small_k_root_is_navier_stokes(self):
        for tau in (1.0, 0.5):
            k = 0.01 / tau
            g = -hydrodynamic_root_M1(k, tau)
            self.assertLess(abs(g - gamma_nse(k, tau)) / gamma_nse(k, tau), 1e-3, tau)

    def test_burnett_correction_reduces_damping_with_unit_coefficient(self):
        q = 0.005
        g = -hydrodynamic_root_M1(q)
        c = -(g / q**2 - 1.0) / q**2
        self.assertAlmostEqual(c, 1.0, delta=2e-3)
        for qq in (0.1, 0.5, 1.0, 1.2):
            self.assertLess(-hydrodynamic_root_M1(qq), gamma_nse(qq))

    def test_M1_and_M2_agree_in_hydrodynamic_range(self):
        for q in np.logspace(-2, np.log10(0.5), 8):
            g1 = -hydrodynamic_root_M1(q)
            g2 = -hydrodynamic_eig_M2(q, 160)[0]
            self.assertLess(abs(g1 - g2) / g1, 1e-3, q)

    def test_damping_bounded_by_collision_rate_and_mode_terminates(self):
        tau = 1.0
        for q in np.linspace(0.05, 1.25, 25):
            r = hydrodynamic_root_M1(q, tau)
            self.assertIsNotNone(r, q)
            self.assertLessEqual(-r, 1.0 / tau + 1e-12)
        self.assertIsNone(hydrodynamic_root_M1(1.26, tau))
        self.assertAlmostEqual(critical_q_M1(tau), Q_CRIT_ANALYTIC, places=8)

    def test_discrete_bgk_operator_is_stable(self):
        """All eigenvalues in [-1/tau, 0]: skew advection plus -(1/tau)(I - P), P an orthogonal projection."""
        for tau in (1.0, 0.3):
            for n in (40, 80, 160):
                for q in (0.1, 1.0, 3.0, 10.0):
                    ev = np.linalg.eigvals(shear_operator(q / tau, n, tau))
                    self.assertLessEqual(float(ev.real.max()), 1e-12)
                    self.assertGreaterEqual(float(ev.real.min()), -1.0 / tau - 1e-10)


if __name__ == "__main__":
    unittest.main()
