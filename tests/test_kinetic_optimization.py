import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock dependencies
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.progress'] = MagicMock()

# Add bridge-python to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

from adapter import MoonlightAdapter, DigitalProprioception

class TestKineticOptimization(unittest.TestCase):

    @patch('adapter.SignalGate')
    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_signal_gate_context(self, mock_which, mock_popen, mock_signal_gate_cls):
        mock_which.return_value = "/usr/bin/cargo"
        mock_gate = mock_signal_gate_cls.return_value
        mock_gate.analyze.return_value = {"ENTROPY": 0.1, "URGENCY": 0.1, "THREAT": 0.0}
        mock_gate.check_veto.return_value = (False, "OK")

        adapter = MoonlightAdapter()
        adapter.gate = mock_gate # Inject mock

        process_mock = MagicMock()
        process_mock.poll.return_value = 0
        process_mock.stdout = MagicMock()
        process_mock.stdout.__iter__.return_value = iter([])
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        # ignite with war_speed=True
        adapter.ignite(war_speed=True)

        mock_gate.analyze.assert_called_with("war_speed")

        # ignite with bench_mode=True
        adapter.ignite(bench_mode=True)
        mock_gate.analyze.assert_called_with("benchmark")

class TestDigitalProprioception(unittest.TestCase):
    def test_audit_execution(self):
        # Fast execution
        success, msg, confidence = DigitalProprioception.audit_execution(0, 1, 2000)
        self.assertTrue(success)
        self.assertEqual(confidence, 1.0)
        self.assertIn("Kinetic Target Met", msg)

        # Slow execution
        success, msg, confidence = DigitalProprioception.audit_execution(0, 1, 500)
        self.assertFalse(success)
        self.assertEqual(confidence, 0.5)
        self.assertIn("Sub-optimal Velocity", msg)

if __name__ == '__main__':
    unittest.main()
