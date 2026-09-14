"""
Unit & Integration Test Suite for Lean 4 Proof-by-Reflection Bridge and Multi-Precision Stepper.
MechanicaFluidorum Program · SocrateAI Lab · September 2026
"""

import os
import sys
import unittest
from fractions import Fraction

# Setup import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
POC_DIR = os.path.join(PROJECT_ROOT, '10_OpenAI_PoC_Proposal')
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, POC_DIR)

from physics_constants import (
    WATER_300K, AIR_300K, HELIUM_GAS_300K,
    SPEED_OF_LIGHT, BOLTZMANN_CONSTANT,
    MACH_INCOMPRESSIBILITY_LIMIT, SONIC_MACH_LIMIT,
    ANISOTROPY_H_DEFAULT, as_dict
)
from asymptotic_multiprecision_stepper import AsymptoticMultiprecisionStepper
from openai_poc_pi_verifier import OpenAIPhysicsVerifier


class TestLeanReflectionBridge(unittest.TestCase):
    """Verifies the Lean 4 Proof-by-Reflection Bridge and exact Rational arithmetic."""

    def setUp(self):
        self.verifier = OpenAIPhysicsVerifier(speed_of_sound=343.0, mach_limit=0.3, knudsen_limit=0.1)

    def test_rational_evaluation_precision(self):
        """Verify that rational arithmetic yields exact fractions without roundoff."""
        # 102.9 m/s in air (c_s = 343.0) -> Mach = 102.9 / 343 = 0.3000 exact
        res = self.verifier.evaluate_trajectory_rational(
            velocity_max=102.9,
            length_scale_min=1e-8,
            enstrophy=500.0
        )
        mach = res["rational_bounds"]["mach"]
        self.assertEqual(mach["num"] / mach["den"], 0.3)
        self.assertTrue(mach["valid"])
        self.assertTrue(res["is_admissible"])

    def test_rational_violation_detection(self):
        """Verify rational evaluation catches violations with exact inequality."""
        # 103.0 m/s in air -> Mach > 0.3
        res = self.verifier.evaluate_trajectory_rational(
            velocity_max=103.0,
            length_scale_min=1e-8,
            enstrophy=500.0
        )
        mach = res["rational_bounds"]["mach"]
        self.assertFalse(mach["valid"])
        self.assertFalse(res["is_admissible"])

    def test_lean_reflection_code_generation(self):
        """Verify the generated Lean 4 code structure and syntactical validity."""
        lean_code = self.verifier.export_lean_reflection_certificate(
            identifier="test_trajectory_alpha",
            velocity_max=85.0,
            length_scale_min=1e-6,
            enstrophy=120.0
        )
        self.assertIn("import Mathlib.Data.Rat.Basic", lean_code)
        self.assertIn("namespace OpenAI.Verification.Reflection", lean_code)
        self.assertIn("def test_trajectory_alpha_mach_rat : Rat", lean_code)
        self.assertIn("def test_trajectory_alpha_is_admissible : Bool", lean_code)
        self.assertIn("#eval test_trajectory_alpha_is_admissible", lean_code)


class TestAsymptoticMultiprecisionStepper(unittest.TestCase):
    """Verifies arbitrary-precision asymptotic singularity stepping."""

    def setUp(self):
        self.stepper = AsymptoticMultiprecisionStepper(dps=80)

    def test_initial_macroscopic_compliance(self):
        """At tau = 1.0 s, the vortex core must be fully physical and compliant."""
        step_1 = self.stepper.step("1.0")
        self.assertEqual(step_1["regime_status"], "COMPLIANT")
        self.assertFalse(step_1["breaches"]["incompressible"])
        self.assertFalse(step_1["breaches"]["sonic"])
        self.assertFalse(step_1["breaches"]["continuum"])
        self.assertFalse(step_1["breaches"]["superluminal"])
        self.assertFalse(step_1["breaches"]["sub_planckian"])

    def test_incompressibility_breach(self):
        """At tau = 1e-14 s, incompressibility must fail (Ma > 0.3)."""
        step = self.stepper.step("1e-14")
        self.assertTrue(step["breaches"]["incompressible"])
        self.assertEqual(step["regime_status"], "INCOMPRESSIBILITY_VIOLATION")

    def test_sonic_shock_breach(self):
        """At tau = 1e-15 s, flow is supersonic (Ma >= 1.0)."""
        step = self.stepper.step("1e-15")
        self.assertTrue(step["breaches"]["sonic"])
        self.assertEqual(step["regime_status"], "SUPERSONIC_SHOCK")

    def test_continuum_breakdown(self):
        """At tau = 1e-18 s, radial scale falls below water intermolecular mean free path."""
        step = self.stepper.step("1e-18")
        self.assertTrue(step["breaches"]["continuum"])
        self.assertEqual(step["regime_status"], "CONTINUUM_BREAKDOWN")

    def test_superluminal_violation(self):
        """At tau = 1e-25 s, peak velocity exceeds the speed of light c."""
        step = self.stepper.step("1e-25")
        self.assertTrue(step["breaches"]["superluminal"])
        self.assertEqual(step["regime_status"], "SUPERLUMINAL_VIOLATION")

    def test_sub_planckian_collapse(self):
        """At tau = 1e-70 s, spatial scale is sub-Planckian."""
        step = self.stepper.step("1e-70")
        self.assertTrue(step["breaches"]["sub_planckian"])
        self.assertEqual(step["regime_status"], "SUB_PLANCKIAN_COLLAPSE")


class TestPhysicsConstants(unittest.TestCase):
    """Verifies consistency of unified physics constants module."""

    def test_fluid_properties_consistency(self):
        """Ensure all standard fluids have positive physical constants."""
        for fluid in [WATER_300K, AIR_300K, HELIUM_GAS_300K]:
            self.assertTrue(fluid.speed_of_sound > 0)
            self.assertTrue(fluid.kinematic_viscosity > 0)
            self.assertTrue(fluid.density > 0)
            self.assertTrue(fluid.mean_free_path > 0)
            # Dynamic viscosity must equal density * kinematic_viscosity
            self.assertAlmostEqual(
                fluid.dynamic_viscosity,
                fluid.density * fluid.kinematic_viscosity,
                places=9
            )

    def test_universal_constants(self):
        """Ensure speed of light and Boltzmann constants match CODATA."""
        self.assertEqual(SPEED_OF_LIGHT, 299792458.0)
        self.assertAlmostEqual(BOLTZMANN_CONSTANT, 1.380649e-23, places=28)

    def test_serialization_dict(self):
        """Ensure serialization dictionary produces valid nested structures."""
        data = as_dict()
        self.assertIn("constants", data)
        self.assertIn("thresholds", data)
        self.assertIn("fluids", data)
        self.assertIn("water", data["fluids"])


if __name__ == '__main__':
    unittest.main()
