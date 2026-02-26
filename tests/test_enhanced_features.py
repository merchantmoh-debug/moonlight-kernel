import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock dependencies
sys.modules['rich'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()

# Add bridge-python to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

from adapter import MoonlightAdapter, SignalGate

class TestEnhancedFeatures(unittest.TestCase):
    def test_validate_kernel_path(self):
        adapter = MoonlightAdapter()
        root = adapter.root_dir

        # Safe paths
        safe_path = os.path.join(root, "core", "lib.wasm")
        safe, msg = adapter.validate_kernel_path(safe_path)
        self.assertTrue(safe, f"Safe path rejected: {msg}")

        # Unsafe paths
        # Note: /etc/passwd might not exist in sandbox, but path logic works on strings mainly
        # os.path.abspath resolves based on CWD.
        unsafe_path = "/etc/passwd"
        safe, msg = adapter.validate_kernel_path(unsafe_path)
        self.assertFalse(safe, "Unsafe path accepted")

        traversal_path = os.path.join(root, "..", "secret.txt")
        safe, msg = adapter.validate_kernel_path(traversal_path)
        self.assertFalse(safe, "Traversal path accepted")

    @patch('adapter.psutil')
    def test_signal_gate_spike(self, mock_psutil):
        gate = SignalGate()

        # Initial state: 10% CPU
        mock_psutil.cpu_percent.return_value = 10.0
        mock_psutil.virtual_memory.return_value.percent = 50.0

        metrics = gate.analyze()
        # Initial context is kinetic_execution -> threat 0.05
        self.assertLess(metrics["THREAT"], 0.5)
        self.assertEqual(gate.last_entropy, 0.1)

        # Spike: 90% CPU (Delta 0.8)
        mock_psutil.cpu_percent.return_value = 90.0

        metrics = gate.analyze()
        self.assertGreaterEqual(metrics["THREAT"], 0.8, "Threat level did not escalate on spike")
        self.assertEqual(gate.last_entropy, 0.9)

if __name__ == '__main__':
    unittest.main()
