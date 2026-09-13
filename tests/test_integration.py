import unittest
import os
import json
import subprocess
import sys

class TestIntegrationPipeline(unittest.TestCase):

    def test_ml_certificate_validity(self):
        """Verify the presence and JSON validity of the ML execution certificate."""
        cert_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../02_Empirical_Observation/DNS_Turbulence_Verification/ML_Turbulence_Execution_Certificate.json'))
        self.assertTrue(os.path.exists(cert_path), "ML Execution certificate does not exist.")
        
        with open(cert_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn("sha256_signature", data)
        self.assertEqual(len(data["sha256_signature"]), 64)
        self.assertIn("metrics", data)

    def test_latex_extractor(self):
        """Test that the limits to latex extraction script executes cleanly."""
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/extract_limits_to_latex.py'))
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Script failed with output: {result.stderr}")
        
        output_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../04_Thermodynamic_Censorship_Paper/physlib_limits_table.tex'))
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn("\\begin{table}", content)

    def test_falsification_graph_generator(self):
        """Test that graph generation script executes cleanly."""
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/generate_falsification_graphs.py'))
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Graph script failed with output: {result.stderr}")

if __name__ == '__main__':
    unittest.main()
