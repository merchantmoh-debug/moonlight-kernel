import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Ensure bridge-python is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

import adapter # Import module to patch its attributes
from adapter import SignalGate, MoonlightAdapter

class TestSignalGate(unittest.TestCase):
    def test_analyze_returns_keys(self):
        # We don't patch psutil here, relying on adapter's internal fallback or mock
        # But if we want consistent tests, we should patch it.
        with patch.object(adapter, 'psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 10.0
            mock_mem = MagicMock()
            mock_mem.percent = 20.0
            mock_psutil.virtual_memory.return_value = mock_mem

            gate = SignalGate()
            metrics = gate.analyze()
            self.assertIn("ENTROPY", metrics)
            self.assertEqual(metrics["ENTROPY"], 0.1)

    def test_high_entropy_veto(self):
        with patch.object(adapter, 'psutil') as mock_psutil:
            # Setup Mock to return specific values
            mock_psutil.cpu_percent.return_value = 95.0
            mock_mem = MagicMock()
            mock_mem.percent = 50.0
            mock_psutil.virtual_memory.return_value = mock_mem

            gate = SignalGate()
            metrics = gate.analyze()

            self.assertAlmostEqual(metrics["ENTROPY"], 0.95)

            veto, reason = gate.check_veto(metrics)
            self.assertTrue(veto)
            self.assertIn("Entropy Critical", reason)

class TestNativeMode(unittest.TestCase):
    def test_native_fallback_selection(self):
        # Patch dependencies in adapter module
        with patch.object(adapter, 'psutil') as mock_psutil, \
             patch.object(adapter.shutil, 'which', return_value="/usr/bin/cargo"), \
             patch.object(adapter.os.path, 'exists', return_value=False), \
             patch.object(adapter.subprocess, 'Popen') as mock_popen, \
             patch.object(adapter.threading, 'Thread'):

            # Setup Psutil Mock
            mock_psutil.cpu_percent.return_value = 10.0
            mock_mem = MagicMock()
            mock_mem.percent = 10.0
            mock_psutil.virtual_memory.return_value = mock_mem

            # Setup Process Mock
            mock_process = MagicMock()
            mock_process.stdout.__iter__.return_value = iter([])
            mock_process.poll.return_value = 0
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            # Instantiate
            moon_adapter = MoonlightAdapter()

            # Run Ignite (suppress print)
            with patch.object(adapter.console, 'print'):
                 moon_adapter.ignite(bench_mode=False, kernel_override=None, strict=False)

            # Verify
            self.assertTrue(mock_popen.called)
            args, kwargs = mock_popen.call_args
            cmd = args[0]

            # Check for Native Mode (no --kernel)
            self.assertNotIn("--kernel", cmd)
            self.assertEqual(cmd[0], "cargo")
            self.assertEqual(cmd[1], "run")

if __name__ == "__main__":
    unittest.main()
