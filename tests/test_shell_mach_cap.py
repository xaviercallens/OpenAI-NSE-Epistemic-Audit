"""
Tests for the Mach-capped dyadic shell model (Lock C proxy).
MechanicaFluidorum Program - SocrateAI Lab - September 2026
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

from shell_mach_cap import (  # noqa: E402
    FLUIDS, MachCappedShellSolver, collapse_crossings, run_cascade, saturation,
)
from dualscale_solver.numeric.dyadic_cascade import DyadicShellSolver  # noqa: E402


class TestSaturation(unittest.TestCase):

    def test_bounds_and_hard_cap(self):
        u = np.array([0.0, 0.5, 1.0, 2.0])
        s = saturation(u, 1.0)
        self.assertTrue(np.all(s >= 0.0) and np.all(s <= 1.0))
        self.assertEqual(s[0], 1.0)
        self.assertEqual(s[2], 0.0)   # exactly zero at c_s: a cap, not a soft roll-off
        self.assertEqual(s[3], 0.0)

    def test_infinite_sound_speed_is_identity(self):
        u = np.linspace(-5, 5, 11)
        self.assertTrue(np.array_equal(saturation(u, np.inf), np.ones_like(u)))


class TestReductionToBase(unittest.TestCase):

    def test_capped_solver_matches_base_when_c_s_infinite(self):
        kw = dict(n_shells=10, k0=1.0, inter_shell_ratio=2.0, nu=1e-4,
                  alpha_prime=None, forcing_shell=0, forcing_amp=1.0)
        base = DyadicShellSolver(**kw)
        capped = MachCappedShellSolver(**kw, c_s=np.inf)
        u0 = np.zeros(10); u0[0] = 1e-3
        a = base.solve((0.0, 2.0), u0, 1e-3)["trajectory"]
        b = capped.solve((0.0, 2.0), u0, 1e-3)["trajectory"]
        self.assertTrue(np.array_equal(a, b))


class TestCascade(unittest.TestCase):

    def test_cap_engages_at_largest_scale(self):
        """In a cascade u_n falls with k, so the Mach cap bites at shell 0."""
        ref = run_cascade(np.inf, nu=1e-4, n_shells=12, t_end=4.0, dt=1e-3, forcing_amp=1.0)
        u0 = ref["u_rms_by_shell"][0]
        self.assertEqual(int(np.argmax(ref["u_rms_by_shell"])), 0)
        r = run_cascade(0.5 * u0, nu=1e-4, n_shells=12, t_end=4.0, dt=1e-3, forcing_amp=1.0)
        self.assertEqual(r["max_mach_shell"], 0)
        self.assertEqual(r["first_engaged_shell"], 0)
        self.assertTrue(r["finite"])


class TestCollapse(unittest.TestCase):

    def test_ma1_crossing_reproduces_paper_scales(self):
        for name, f in FLUIDS.items():
            c = collapse_crossings(f["nu"], f["c_s"])
            self.assertAlmostEqual(c["l_at_Ma1_over_l_star"], 1.0, delta=1e-2, msg=name)
            self.assertAlmostEqual(c["t_at_Ma1_over_t_star"], 1.0, delta=1e-2, msg=name)
        # the headline numbers quoted in the paper
        w = collapse_crossings(**FLUIDS["water"])
        self.assertAlmostEqual(w["Ma_1"]["l_m"] / 0.67e-9, 1.0, delta=0.01)
        self.assertAlmostEqual(w["Ma_1"]["t_s"] / 0.44e-12, 1.0, delta=0.02)
        a = collapse_crossings(**FLUIDS["air"])
        self.assertAlmostEqual(a["Ma_1"]["l_m"] / 45e-9, 1.0, delta=0.02)
        self.assertAlmostEqual(a["Ma_1"]["t_s"] / 0.13e-9, 1.0, delta=0.03)


if __name__ == "__main__":
    unittest.main()
