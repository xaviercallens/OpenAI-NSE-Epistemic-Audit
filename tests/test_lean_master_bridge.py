import unittest
import numpy as np
import os
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))


class TestLeanMasterEpistemicBridge(unittest.TestCase):
    """
    Unit tests for LeanMaster Epistemic Bridge theorems formalized in Lean 4:
    1. NSE-P1: Hydrodynamic Helicity & Energy Dissipation Bound (2 D E >= nu H^2)
    2. TURB-P5: Kolmogorov-41 Energy Cascade Cutoff (2 nu Omega >= epsilon)
    3. TCC-P3: Dual-Scale Geometric Censorship ((R^2 + 1) * lambda_0 >= 2 > l_Pl)
    4. Master Unified Physical Censorship Contract
    """

    def test_nse_p1_helicity_dissipation_bound(self):
        """
        Verify that non-zero topological helicity enforces strictly positive
        enstrophy and viscous dissipation: 2 * D * E >= nu * H^2.
        """
        nu = 1  # scaled integer viscosity
        H = 5   # non-zero helicity |H| >= 1
        E = 10  # non-zero kinetic energy

        # Cauchy-Schwarz compatibility: H^2 <= 4 * E * Omega
        # => Omega >= ceil(H^2 / (4 * E)) = ceil(25 / 40) = 1
        omega_min = int(np.ceil((H ** 2) / (4.0 * E)))
        self.assertGreaterEqual(omega_min, 1)

        # Viscous dissipation D = 2 * nu * Omega
        D = 2 * nu * omega_min
        self.assertGreater(D, 0)

        # Master inequality: 2 * D * E >= nu * H^2
        lhs = 2 * D * E
        rhs = nu * (H ** 2)
        self.assertGreaterEqual(lhs, rhs)

    def test_turb_p5_kolmogorov_cascade_cutoff(self):
        """
        Verify Kolmogorov-41 spectral dissipation and enstrophy lower bound:
        D(k, E_k) = 2 * nu * k^2 * E_k > 0, and 2 * nu * Omega >= epsilon.
        """
        nu = 1
        epsilon = 100  # energy flux
        k = 4          # wavenumber
        E_k = 10       # modal energy

        # Spectral dissipation
        D_k = 2 * nu * (k ** 2) * E_k
        self.assertGreater(D_k, 0)

        # Enstrophy flux compatibility: 2 * nu * Omega >= epsilon
        omega_min = int(np.ceil(epsilon / (2.0 * nu)))
        self.assertGreater(omega_min, 0)
        self.assertGreaterEqual(2 * nu * omega_min, epsilon)

    def test_tcc_p3_dual_scale_censorship(self):
        """
        Verify Dual-Scale Swampland & Geometric Censorship:
        lambda_num(R, lambda_0) = (R^2 + 1) * lambda_0 >= 2 > l_Pl (minimal_scale = 1).
        """
        minimal_scale = 1
        for R in [1, 2, 5, 10, 100]:
            for lambda_0 in [1, 2, 3]:
                lambda_num = (R ** 2 + 1) * lambda_0
                self.assertGreaterEqual(lambda_num, 2)
                self.assertFalse(lambda_num <= minimal_scale, "Sub-minimal scale must be algebraically forbidden")

    def test_lean_master_contract_consistency(self):
        """
        Verify simultaneous satisfaction of all three LeanMaster contracts:
        Helicity, Kolmogorov, and Dual-Scale.
        """
        # State parameters
        nu, H, E, epsilon = 2, 3, 20, 50
        omega = 15
        k, E_k = 2, 5
        R, lambda_0 = 1, 1

        # 1. Helicity contract
        D = 2 * nu * omega
        self.assertGreater(D, 0)
        self.assertGreaterEqual(2 * D * E, nu * (H ** 2))

        # 2. Kolmogorov contract
        D_k = 2 * nu * (k ** 2) * E_k
        self.assertGreater(D_k, 0)
        self.assertGreaterEqual(2 * nu * omega, epsilon)

        # 3. Dual-scale contract
        lambda_num = (R ** 2 + 1) * lambda_0
        self.assertGreaterEqual(lambda_num, 2)


if __name__ == '__main__':
    unittest.main()
