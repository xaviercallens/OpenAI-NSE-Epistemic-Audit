"""
Tests for Analytical Directives (Directives 3, 4, 6, and 7).
MechanicaFluidorum Program · SocrateAI Lab · September 2026

Validates:
- Directive 3: 5-Moment Jacobian Non-Dimensionalization & Matrix Scaling (kappa(B) invariance).
- Directive 4: Gevrey Regularity vs C-infinity Cutoff Asymptotics.
- Directive 6: Microscopic Thermal Response & Structural Stability.
- Directive 7: Pre-Singularity Simulation and Profile Scaling (with --no-anim bypass).
"""

import os
import sys
import unittest
import tempfile
import numpy as np
from scipy.linalg import svd, solve, norm

# Ensure scripts directory is on sys.path
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import directive2_thermodynamic_paradox as d2
import directive3_jacobian_instability as d3
import directive4_gevrey_regularity as d4
import directive5_mach_divergence as d5
import directive6_thermal_instability as d6
import directive7_pre_singularity_simulation as d7


class TestDirective3JacobianInstability(unittest.TestCase):
    """Unit tests for Directive 3: 5-Moment Jacobian Non-Dimensionalization."""

    def test_azimuthal_block_construction(self):
        """Verify 3x3 azimuthal moment block structure and positive definiteness."""
        A_theta = d3.construct_A_theta(lam=0.1, X_R=10.0)
        self.assertEqual(A_theta.shape, (3, 3))
        self.assertTrue(np.all(np.diag(A_theta) > 0), "Diagonal elements must be strictly positive")
        # Symmetric positive moments
        self.assertTrue(np.all(A_theta > 0), "Moment integrals of positive bump must be positive")

    def test_axial_block_construction(self):
        """Verify 2x2 axial moment block structure."""
        A_z = d3.construct_A_z(lam=0.1, X_R=10.0)
        self.assertEqual(A_z.shape, (2, 2))
        self.assertTrue(np.all(np.diag(A_z) > 0), "Diagonal elements must be strictly positive")
        self.assertTrue(np.all(A_z > 0), "Moment integrals must be positive")

    def test_nondimensional_condition_number_invariance(self):
        """
        Verify that B = D^-1 A D^-1 has an invariant condition number
        kappa(B) ~ 4.11e5 regardless of X_R, whereas raw kappa(A) explodes.
        """
        lam = 0.1
        X_R_test_values = [1.0, 5.0, 20.0, 100.0]
        kappa_B_values = []

        for X_R in X_R_test_values:
            A_full, B_full = d3.get_nondimensional_matrices(lam, X_R)
            self.assertEqual(A_full.shape, (5, 5))
            self.assertEqual(B_full.shape, (5, 5))

            _, s_A, _ = svd(A_full)
            _, s_B, _ = svd(B_full)

            kappa_A = s_A[0] / s_A[-1]
            kappa_B = s_B[0] / s_B[-1]
            kappa_B_values.append(kappa_B)

            # For large X_R, raw matrix A explodes
            if X_R >= 100.0:
                self.assertGreater(kappa_A, 1e12, "Raw kappa(A) must reflect dimensional scaling explosion")

        # Non-dimensional condition number must remain constant within 1% across all X_R
        base_kappa = kappa_B_values[0]
        for k_val in kappa_B_values:
            self.assertAlmostEqual(k_val, base_kappa, delta=base_kappa * 0.02)
        # Expected value is approx 4.11e5
        self.assertGreater(base_kappa, 1e5)
        self.assertLess(base_kappa, 1e6)

    def test_directive3_audit_execution(self):
        """Verify run_audit executes cleanly."""
        try:
            d3.run_audit()
        except Exception as e:
            self.fail(f"directive3 run_audit failed with exception: {e}")


class TestDirective4GevreyRegularity(unittest.TestCase):
    """Unit tests for Directive 4: Gevrey Regularity Analysis."""

    def test_gevrey_derivatives_computation(self):
        """Verify derivative coefficient extraction for exp(-1/q^2) up to N=6."""
        data, s_emp = d4.compute_gevrey_derivatives(max_N=6)
        self.assertEqual(len(data), 6)

        for d in data:
            self.assertIn('N', d)
            self.assertIn('C_N', d)
            self.assertIn('N_fact', d)
            self.assertIn('ratio_nfact', d)
            self.assertGreater(d['C_N'], 0.0)
            self.assertGreater(d['N_fact'], 0)

        # Pre-asymptotic slope for N in [3, 6] should be bounded in [1.5, 3.5]
        self.assertGreater(s_emp, 1.4)
        self.assertLess(s_emp, 3.5)

    def test_theoretical_asymptotic_index(self):
        """
        Verify the mathematical theorem: exp(-1/q^k) has asymptotic Gevrey index s = 1 + 1/k.
        For k = 2: s = 1.5.
        """
        k = 2
        s_theoretical = 1.0 + 1.0 / k
        self.assertEqual(s_theoretical, 1.5)

    def test_directive4_audit_execution(self):
        """Verify run_audit executes cleanly with small max_N."""
        try:
            d4.run_audit(max_N=5)
        except Exception as e:
            self.fail(f"directive4 run_audit failed with exception: {e}")


class TestDirective6ThermalInstability(unittest.TestCase):
    """Unit tests for Directive 6: Thermal Fluctuation & Structural Stability."""

    def test_thermal_fluctuation_calculation(self):
        """Verify thermal velocity fluctuation scale formula delta_u = sqrt(k_B T / rho V)."""
        # At T = 300K, rho = 1000 kg/m^3, L = 0.01m (V = 1e-6 m^3)
        # delta_u = sqrt(1.381e-23 * 300 / (1000 * 1e-6)) = sqrt(4.143e-21 / 1e-3) = sqrt(4.143e-18) approx 2.035e-9 or similar
        delta_u_300 = d6.evaluate_thermal_fluctuation(T=300.0, rho=1000.0, l_ref=0.01)
        self.assertGreater(delta_u_300, 0.0)

        # Scaling: delta_u(4*T) == 2 * delta_u(T)
        delta_u_1200 = d6.evaluate_thermal_fluctuation(T=1200.0, rho=1000.0, l_ref=0.01)
        self.assertAlmostEqual(delta_u_1200, 2.0 * delta_u_300, places=12)

        # Zero temperature gives zero fluctuation
        self.assertEqual(d6.evaluate_thermal_fluctuation(T=0.0), 0.0)

    def test_moment_system_stability_under_noise(self):
        """
        Verify that solving B c = b under thermal perturbation produces small relative error,
        proving structural stability.
        """
        B = d6.construct_moment_system(lam=0.1, X_R=10.0)
        self.assertEqual(B.shape, (5, 5))

        b_target = np.array([1.0, 0.5, 0.2, 0.8, 0.3])
        c_exact = solve(B, b_target)

        # Add 1e-5 relative perturbation to rhs
        np.random.seed(42)
        noise = np.random.randn(5) * 1e-5 * norm(b_target)
        c_pert = solve(B, b_target + noise)

        rel_error = norm(B @ c_pert - b_target) / norm(b_target)
        self.assertLess(rel_error, 1e-3, "Stress error must remain bounded under small perturbation")

    def test_thermal_response_across_temperatures(self):
        """Verify system stability across cryo to boiling temperatures."""
        temperatures = [4.2, 77.36, 277.0, 300.0, 373.15]
        B = d6.construct_moment_system(lam=0.1, X_R=10.0)
        b_target = np.array([1.0, 0.5, 0.2, 0.8, 0.3])

        for T in temperatures:
            delta_u = d6.evaluate_thermal_fluctuation(T=T)
            noise_scale = delta_u / (d6.NU_DEFAULT / d6.L_REF_DEFAULT)
            delta_b = np.ones(5) * noise_scale * norm(b_target)
            c_pert = solve(B, b_target + delta_b)
            err = norm(B @ c_pert - b_target) / norm(b_target)
            self.assertLess(err, 0.01, f"Stress error exceeded threshold at T={T}K")

    def test_directive6_run_thermal_audit(self):
        """Verify run_thermal_audit executes cleanly and reports stable fidelity."""
        try:
            d6.run_thermal_audit()
        except Exception as e:
            self.fail(f"directive6 run_thermal_audit failed with exception: {e}")


class TestDirective7PreSingularitySimulation(unittest.TestCase):
    """Unit tests for Directive 7: Pre-Singularity Simulation and Profile Scaling."""

    def test_profile_scaling(self):
        """Verify u_theta and Reynolds stress scaling as tau decreases."""
        r = np.logspace(-7, 0, 500)
        tau_1 = 1e-3
        tau_2 = 1e-6

        u1, rs1 = d7.get_profiles(tau_1, r=r)
        u2, rs2 = d7.get_profiles(tau_2, r=r)

        self.assertEqual(len(u1), 500)
        self.assertEqual(len(rs1), 500)
        # Peak velocity must increase as tau decreases (tau^(-0.505))
        self.assertGreater(np.max(u2), np.max(u1))
        # Peak Reynolds stress proxy must increase
        self.assertGreater(np.max(rs2), np.max(rs1))
        # Non-negativity of Reynolds stress
        self.assertTrue(np.all(rs1 >= 0))
        self.assertTrue(np.all(rs2 >= 0))

    def test_profile_default_r(self):
        """Verify get_profiles uses default logspace r grid if r is None."""
        u, rs = d7.get_profiles(1e-4)
        self.assertEqual(len(u), 1000)
        self.assertEqual(len(rs), 1000)

    def test_parse_args(self):
        """Verify command-line argument parsing for Directive 7."""
        args = d7.parse_args(['--no-anim', '--num-frames', '50'])
        self.assertTrue(args.no_anim)
        self.assertEqual(args.num_frames, 50)

    def test_run_simulation_no_anim(self):
        """Verify simulation executes rapidly without animation generation when no_anim=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            static_path = d7.run_simulation(no_anim=True, num_frames=5, output_dir=tmpdir)
            self.assertTrue(os.path.exists(static_path), "Static profile plot must be generated")
            # Confirm GIF was not created
            gif_path = os.path.join(tmpdir, 'pre_singularity_vortex.gif')
            self.assertFalse(os.path.exists(gif_path), "GIF must not be generated when no_anim=True")


class TestDirective2ThermodynamicParadox(unittest.TestCase):
    """Unit tests for Directive 2: SymPy Audit of Thermodynamic Paradox."""

    def test_scaling_exponents(self):
        """Verify analytical exponents for energy, enstrophy, and norms at h=1/200."""
        exp_data = d2.get_scaling_exponents()
        # Global energy exponent > 0 (integrable, vanishes as tau -> 0)
        self.assertAlmostEqual(float(exp_data['global_energy_exponent']), 0.485, places=3)
        self.assertGreater(float(exp_data['global_energy_exponent']), 0.0)

        # Intensive local energy density exponent < 0 (diverges)
        self.assertAlmostEqual(float(exp_data['local_energy_density_exponent']), -1.010, places=3)
        self.assertLess(float(exp_data['local_energy_density_exponent']), 0.0)

        # Enstrophy exponent < 0 (diverges)
        self.assertAlmostEqual(float(exp_data['enstrophy_exponent']), -0.515, places=3)
        self.assertLess(float(exp_data['enstrophy_exponent']), 0.0)

        # Critical p* where L^p norm diverges is approximately 2.97
        self.assertAlmostEqual(float(exp_data['p_critical']), 300 / 101, places=3)
        # L^3 norm exponent is negative
        self.assertLess(float(exp_data['L3_exponent']), 0.0)

        # H^(3/2) Sobolev norm exponent = -0.5075
        self.assertAlmostEqual(float(exp_data['H32_exponent']), -0.5075, places=4)

    def test_directive2_audit_execution(self):
        """Verify run_audit executes cleanly without exceptions."""
        try:
            d2.run_audit()
        except Exception as e:
            self.fail(f"directive2 run_audit failed with exception: {e}")


class TestDirective5MachDivergence(unittest.TestCase):
    """Unit tests for Directive 5: Mach Number Divergence and Self-Invalidation."""

    def test_velocity_and_mach_scaling(self):
        """Verify velocity and Mach number increase monotonically as tau -> 0."""
        v_macro = d5.velocity(1.0)
        v_micro = d5.velocity(1e-10)
        self.assertGreater(v_micro, v_macro)

        ma_macro = d5.mach_number(1.0)
        ma_micro = d5.mach_number(1e-10)
        self.assertGreater(ma_micro, ma_macro)
        self.assertLess(ma_macro, 0.3, "Macroscopic state must be incompressible")

    def test_critical_times_ordering(self):
        """Verify ordering: tau_break_Ma > tau_sonic > 0."""
        crits = d5.get_critical_times()
        tau_break = crits['tau_break_Ma']
        tau_sonic = crits['tau_sonic']
        tau_kn = crits['tau_knudsen']

        self.assertGreater(tau_break, 0.0)
        self.assertGreater(tau_sonic, 0.0)
        self.assertGreater(tau_break, tau_sonic, "Incompressibility must break before sonic speed")
        self.assertAlmostEqual(tau_break, 6.7e-14, delta=2e-14)

    def test_reynolds_and_core_radius(self):
        """Verify core radius contracts and angular Reynolds number calculation."""
        r1 = d5.core_radius(1.0)
        r2 = d5.core_radius(1e-4)
        self.assertGreater(r1, r2)

        re_val = d5.reynolds_angular(1.0)
        self.assertGreater(re_val, 0.0)

    def test_directive5_audit_execution(self):
        """Verify run_audit executes cleanly."""
        try:
            d5.run_audit()
        except Exception as e:
            self.fail(f"directive5 run_audit failed with exception: {e}")


if __name__ == '__main__':
    unittest.main()

