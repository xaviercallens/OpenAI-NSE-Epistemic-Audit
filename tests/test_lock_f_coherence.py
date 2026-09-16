"""
Tests for the Lock F coherent-packet experiment.
MechanicaFluidorum Program - SocrateAI Lab - September 2026

- The seeded packet field is real in physical space and solenoidal.
- With theta = 0 the ensemble coherent fraction is exactly 1.
- The exponential-fit helper recovers a known decoherence time.
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
from lock_f_coherence import (  # noqa: E402
    coherent_fraction, evolve, fit_decoherence_time, packet_amplitude, seed_packet,
)


class TestSeededPacket(unittest.TestCase):

    def test_seeded_field_is_real_and_solenoidal(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u_hat, e = seed_packet(s, s.initialize_taylor_green(), (3, 2, 1), 0.01, 0.7)
        phys = np.stack([np.fft.ifftn(u_hat[j]) for j in range(3)])
        self.assertLess(float(np.max(np.abs(phys.imag))) / float(np.max(np.abs(phys.real))), 1e-12)
        self.assertLess(s.divergence_report(u_hat)["div_l2_relative"], 1e-12)
        a = packet_amplitude(s, u_hat, (3, 2, 1), e)
        self.assertAlmostEqual(abs(a), 0.01, places=12)
        self.assertAlmostEqual(np.angle(a), 0.7, places=12)


class TestCoherenceControls(unittest.TestCase):

    def test_zero_temperature_keeps_coherent_fraction_at_one(self):
        s = PseudoSpectralNavierStokes3D(n_grid=16, nu=1e-2)
        u_hat, e = seed_packet(s, s.initialize_taylor_green(), (3, 2, 1), 0.01, 0.3)
        members = [evolve(s, u_hat, 0.02, 5, 0.0, None, (3, 2, 1), e)[1] for _ in range(3)]
        f = coherent_fraction(np.array(members))
        self.assertLess(float(np.max(np.abs(f - 1.0))), 1e-12)


class TestFitHelper(unittest.TestCase):

    def test_recovers_known_exponential(self):
        t = np.linspace(0.0, 3.0, 61)
        f = np.exp(-t / 2.0)
        fit = fit_decoherence_time(t, f)
        self.assertAlmostEqual(fit["tau_decoh"], 2.0, places=9)
        self.assertGreater(fit["r_squared"], 1.0 - 1e-12)


if __name__ == "__main__":
    unittest.main()
