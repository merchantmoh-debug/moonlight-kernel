import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add bridge-python to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

from adapter import SignalGate, MoonlightAdapter

class TestMoonlightAdapter(unittest.TestCase):
    def test_signal_gate(self):
        gate = SignalGate()
        metrics = gate.analyze()
        self.assertIn("ENTROPY", metrics)
        self.assertIn("URGENCY", metrics)
        self.assertIn("THREAT", metrics)

        # Test Veto
        metrics["ENTROPY"] = 0.95
        veto, reason = gate.check_veto(metrics)
        self.assertTrue(veto)
        self.assertIn("Critical", reason)

        metrics["ENTROPY"] = 0.1
        veto, reason = gate.check_veto(metrics)
        self.assertFalse(veto)

    @patch("adapter.shutil.which")
    @patch("adapter.os.path.exists")
    @patch("adapter.subprocess.Popen")
    def test_ignite_flow(self, mock_popen, mock_exists, mock_which):
        # Mock environment
        mock_which.side_effect = lambda x: "/usr/bin/" + x
        mock_exists.return_value = True # Pretend kernel exists

        mock_process = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout.__iter__.return_value = ["INFO: Neuronal Validation: ACTIVE", "BENCHMARK: 1000"]
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        adapter = MoonlightAdapter()

        # We need to mock TUI or run in headless mode.
        # Adapter checks sys.stdout.isatty(). Let's mock it to False.
        with patch("sys.stdout.isatty", return_value=False):
            adapter.ignite(bench_mode=True)

        # Verify Popen called correctly
        mock_popen.assert_called()
        args, kwargs = mock_popen.call_args
        cmd = args[0]
        self.assertIn("cargo", cmd)
        self.assertIn("run", cmd)
        self.assertIn("--bench", cmd)
        self.assertIn("--kernel", cmd)

if __name__ == "__main__":
    unittest.main()
