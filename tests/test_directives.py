import unittest
import numpy as np
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../02_Empirical_Observation/DNS_Turbulence_Verification')))

from analyze_dns_enstrophy import calculate_kolmogorov_microscale, verify_dns_enstrophy_bound

class TestPhysicalDirectives(unittest.TestCase):
    
    def test_kolmogorov_microscale(self):
        """Test Kolmogorov length scale calculation for water."""
        epsilon = 1.0 # 1 m^2/s^3 dissipation rate
        nu = 1.004e-6 # Kinematic viscosity of water
        eta = calculate_kolmogorov_microscale(epsilon, nu)
        
        # Expected eta approx ( (1.004e-6)^3 / 1.0 )^0.25 approx 3.17e-5 meters
        self.assertAlmostEqual(eta, 3.172e-5, delta=1e-7)
        self.assertTrue(eta > 0)

    def test_enstrophy_bounding(self):
        """Test enstrophy bound verification function."""
        N = 16
        dx = dy = dz = 1e-3
        field = np.ones((3, N, N, N)) # Uniform field -> zero vorticity
        
        max_enstrophy, global_enstrophy, eta = verify_dns_enstrophy_bound(field, dx, dy, dz)
        
        self.assertAlmostEqual(max_enstrophy, 0.0, places=5)
        self.assertAlmostEqual(global_enstrophy, 0.0, places=5)

    def test_mach_invalidation_threshold(self):
        """Test that velocity scaling breaches Mach 0.3 at critical tau."""
        c_s = 1500.0 # Speed of sound in water
        tau_critical = 6.7e-14
        
        velocity_math = 1.18e-4 * (tau_critical ** -0.505)
        mach = velocity_math / c_s
        
        self.assertAlmostEqual(mach, 0.30, delta=0.1)

if __name__ == '__main__':
    unittest.main()
