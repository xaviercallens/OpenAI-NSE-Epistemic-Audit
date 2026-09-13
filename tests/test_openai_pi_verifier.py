"""
Unit & Integration Test Suite for OpenAI Physics-Informed Verifier (PI-Verifier)
MechanicaFluidorum Program · SocrateAI Lab · September 2026

Demonstrates that the PI-Verifier correctly detects and rejects trajectories
that violate physical laws (Mach limit, Knudsen continuum limit, 2nd Law of Thermodynamics).
"""

import os
import sys
import unittest

# Add project root and PoC directory to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
POC_DIR = os.path.join(PROJECT_ROOT, '10_OpenAI_PoC_Proposal')
sys.path.insert(0, POC_DIR)

from openai_poc_pi_verifier import OpenAIPhysicsVerifier


class TestOpenAIPhysicsVerifier(unittest.TestCase):

    def setUp(self):
        """Initialize the Physics Verifier with standard physical thresholds."""
        self.verifier = OpenAIPhysicsVerifier(speed_of_sound=343.0, mach_limit=0.3, knudsen_limit=0.1)

    def test_mach_number_violation_rejection(self):
        """Rule 1: Trajectories breaching Mach 0.3 must be REJECTED."""
        # Velocity 450 m/s in air -> Mach 1.31 > 0.3
        res = self.verifier.evaluate_trajectory(velocity_max=450.0, length_scale_min=1e-6, enstrophy=100.0)
        self.assertFalse(res['admissibility_checks']['mach_condition_passed'])
        self.assertEqual(res['verdict'], 'UNPHYSICAL_BLOWUP_REJECTED')
        self.assertIn('breaches physical continuum boundaries', res['epistemic_recommendation'])

    def test_knudsen_continuum_breakdown_rejection(self):
        """Rule 2: Sub-nanometer length scales breaching Knudsen limit (Kn > 0.1) must be REJECTED."""
        # Length scale 1e-12 m -> Kn = 1000 >> 0.1 (Continuum hypothesis breakdown)
        res = self.verifier.evaluate_trajectory(velocity_max=50.0, length_scale_min=1e-12, enstrophy=100.0)
        self.assertFalse(res['admissibility_checks']['knudsen_condition_passed'])
        self.assertEqual(res['verdict'], 'UNPHYSICAL_BLOWUP_REJECTED')

    def test_entropy_second_law_violation_rejection(self):
        """Rule 3: Negative entropy production violating Second Law of Thermodynamics must be REJECTED."""
        # Negative enstrophy / negative entropy generation
        res = self.verifier.evaluate_trajectory(velocity_max=50.0, length_scale_min=1e-6, enstrophy=-500.0)
        self.assertFalse(res['admissibility_checks']['entropy_second_law_passed'])
        self.assertEqual(res['verdict'], 'UNPHYSICAL_BLOWUP_REJECTED')

    def test_physically_admissible_trajectory_acceptance(self):
        """Verify that a physically realistic fluid trajectory passes all checks."""
        # Subsonic velocity (85 m/s, Mach 0.25), continuum scale (1e-6 m), positive dissipation
        res = self.verifier.evaluate_trajectory(velocity_max=85.0, length_scale_min=1e-6, enstrophy=120.0)
        self.assertTrue(res['admissibility_checks']['mach_condition_passed'])
        self.assertTrue(res['admissibility_checks']['knudsen_condition_passed'])
        self.assertTrue(res['admissibility_checks']['entropy_second_law_passed'])
        self.assertEqual(res['verdict'], 'PHYSICALLY_ADMISSIBLE')

    def test_certificate_generation(self):
        """Integration Test: Ensure certificate JSON is successfully written."""
        cert_path = os.path.join(PROJECT_ROOT, "scratch_test_certificate.json")
        cert = self.verifier.generate_certificate(output_path=cert_path)
        self.assertTrue(os.path.exists(cert_path))
        self.assertIn("openai_unconstrained_sobolev_proof", cert["scenarios"])
        self.assertEqual(cert["scenarios"]["openai_unconstrained_sobolev_proof"]["verdict"], "UNPHYSICAL_BLOWUP_REJECTED")
        self.assertEqual(cert["scenarios"]["leanflow_dual_scale_proof"]["verdict"], "PHYSICALLY_ADMISSIBLE")

        # Cleanup scratch file
        if os.path.exists(cert_path):
            os.remove(cert_path)


if __name__ == '__main__':
    unittest.main()
