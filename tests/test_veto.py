import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock dependencies for headless testing
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['psutil'] = MagicMock()

# Add bridge-python to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

# Import adapter after path adjust
from adapter import SignalGate

class TestSignalGate(unittest.TestCase):
    def setUp(self):
        self.gate = SignalGate()

    def test_veto_logic_entropy(self):
        # Simulate high CPU
        metrics = {"ENTROPY": 0.95, "URGENCY": 0.5, "THREAT": 0.0}
        veto, reason = self.gate.check_veto(metrics)
        self.assertTrue(veto)
        self.assertIn("Thermodynamic Limit Reached", reason)

    def test_veto_logic_urgency(self):
        # Simulate high RAM
        metrics = {"ENTROPY": 0.5, "URGENCY": 0.96, "THREAT": 0.0}
        veto, reason = self.gate.check_veto(metrics)
        self.assertTrue(veto)
        self.assertIn("OOM Risk Imminent", reason)

    def test_veto_logic_threat_strict(self):
        # Simulate High Threat in Strict Mode
        metrics = {"ENTROPY": 0.5, "URGENCY": 0.5, "THREAT": 0.8}
        veto, reason = self.gate.check_veto(metrics, strict=True)
        self.assertTrue(veto)
        self.assertIn("Operational Risk too high", reason)

    def test_no_veto_threat_lax(self):
        # Simulate High Threat in Lax Mode
        metrics = {"ENTROPY": 0.5, "URGENCY": 0.5, "THREAT": 0.8}
        veto, reason = self.gate.check_veto(metrics, strict=False)
        self.assertFalse(veto)

if __name__ == '__main__':
    unittest.main()
