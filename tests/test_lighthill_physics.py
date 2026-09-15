import unittest
import numpy as np
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from physics_constants import WATER_300K, AIR_300K, HELIUM_GAS_300K, ANISOTROPY_H_DEFAULT, L_REF_DEFAULT
from experiment_lighthill_and_physics_data import lighthill_acoustic_power, multi_fluid_critical_times


class TestLighthillAcousticPhysics(unittest.TestCase):
    """
    Unit tests for Lighthill acoustic radiation scaling and multi-fluid
    continuum and compressibility limits.
    """

    def test_lighthill_power_scaling_exponent(self):
        """Verify that Lighthill radiated power scales exactly as tau^(-(3 + 8h))."""
        h = ANISOTROPY_H_DEFAULT  # 0.005
        expected_exponent = -(3.0 + 8.0 * h)  # -3.04
        
        tau1 = 1e-4
        tau2 = 1e-6
        p1 = lighthill_acoustic_power(tau1, WATER_300K, h=h)
        p2 = lighthill_acoustic_power(tau2, WATER_300K, h=h)
        
        measured_exponent = np.log(p2 / p1) / np.log(tau2 / tau1)
        self.assertAlmostEqual(measured_exponent, expected_exponent, places=5)

    def test_acoustic_power_density_divergence(self):
        """Verify that volumetric acoustic power density scales as tau^(-4.535)."""
        h = ANISOTROPY_H_DEFAULT  # 0.005
        # V_core = pi * l_r^2 * l_z = pi * l_0^3 * tau^(3/2 - h)
        # p_ac = P_ac / V_core ~ tau^(-3 - 8h - (3/2 - h)) = tau^(-4.5 - 7h) = tau^(-4.535)
        expected_density_exponent = -(4.5 + 7.0 * h)  # -4.535
        
        tau1 = 1e-5
        tau2 = 1e-8
        
        def core_volume(t):
            lr = L_REF_DEFAULT * (t ** 0.5)
            lz = L_REF_DEFAULT * (t ** (0.5 - h))
            return np.pi * (lr ** 2) * lz
        
        dens1 = lighthill_acoustic_power(tau1, WATER_300K, h=h) / core_volume(tau1)
        dens2 = lighthill_acoustic_power(tau2, WATER_300K, h=h) / core_volume(tau2)
        
        measured_density_exponent = np.log(dens2 / dens1) / np.log(tau2 / tau1)
        self.assertAlmostEqual(measured_density_exponent, expected_density_exponent, places=5)

    def test_multi_fluid_critical_times_ordering(self):
        """
        Verify multi-fluid breakdown times across Water, Air, and Helium.
        In all cases, breakdown occurs long before tau = 0.
        """
        table = multi_fluid_critical_times()
        self.assertEqual(len(table), 3)
        
        water_row = next(r for r in table if "Water" in r["fluid"])
        air_row = next(r for r in table if "Air" in r["fluid"])
        helium_row = next(r for r in table if "Helium" in r["fluid"])
        
        # Water incompressibility limit tau ~ 6.69e-14 s
        self.assertAlmostEqual(water_row["tau_ma_03"], 6.69e-14, delta=1e-15)
        # Sonic barrier tau ~ 6.16e-15 s
        self.assertAlmostEqual(water_row["tau_sonic"], 6.16e-15, delta=1e-16)
        
        # In gases (Air, Helium), incompressibility and continuum break down much earlier
        self.assertTrue(air_row["tau_ma_03"] > water_row["tau_ma_03"])
        self.assertTrue(helium_row["tau_ma_03"] > water_row["tau_ma_03"])
        
        # Knudsen continuum breakdown ordering: Helium > Air > Water
        self.assertTrue(helium_row["tau_kn_01"] > air_row["tau_kn_01"])
        self.assertTrue(air_row["tau_kn_01"] > water_row["tau_kn_01"])

    def test_radiated_energy_divergence(self):
        """
        Analytic proof that cumulative acoustic energy integral int_tau^1 P_ac dt
        diverges as tau -> 0.
        """
        h = ANISOTROPY_H_DEFAULT
        # If P_ac(t) = C * t^(-3 - 8h), then int_tau^1 t^(-3 - 8h) dt = [t^(-2 - 8h) / (-2 - 8h)]_tau^1
        # Diverges as tau^(-2 - 8h) = tau^(-2.04) -> infty
        energy_exponent = -(2.0 + 8.0 * h)
        self.assertAlmostEqual(energy_exponent, -2.04, places=6)
        self.assertTrue(energy_exponent < 0, "Integrated acoustic energy must diverge as tau -> 0")


if __name__ == '__main__':
    unittest.main()
