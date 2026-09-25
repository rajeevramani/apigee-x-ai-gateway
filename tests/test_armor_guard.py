"""Behavioral checks of the shipped validator, not native runtime qualification."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('node'), 'Node.js is required for the validator checks')
class ArmorGuard(unittest.TestCase):
    def test_native_json_contract(self):
        result = subprocess.run(['node', str(ROOT / 'tests/test_armor_guard.cjs'),
            str(ROOT / 'assets/examples/model-armor/validate-armor.js')],
            text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Model Armor guard checks passed', result.stdout)
