import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import subprocess

# Add bridge-python to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../bridge-python')))

# Mock rich before importing adapter if needed, but adapter handles it.
from adapter import MoonlightAdapter, SignalGate

class TestKineticIntegrity(unittest.TestCase):
    def setUp(self):
        self.adapter = MoonlightAdapter()

    def test_veto_logic(self):
        """Verify that high entropy triggers a SystemError (Panic)."""
        print("\nTesting Veto Logic...")
        # Mock psutil to return 100% CPU
        with patch('adapter.psutil') as mock_psutil:
            mock_psutil.cpu_percent.return_value = 99.9
            mock_psutil.virtual_memory.return_value.percent = 50.0

            # Re-initialize gate to use mocked psutil if needed,
            # but adapter imports psutil at module level.
            # We need to patch the module where adapter imported it.
            # Actually, `from adapter import psutil` isn't how it works.
            # It's `import psutil`.

            # Analyze
            metrics = self.adapter.gate.analyze()
            # print(f"Metrics: {metrics}")

            # The threshold is > 0.90 in adapter logic?
            # Wait, I set logic: if veto: raise SystemError.
            # check_veto returns True if entropy > 0.90.

            self.assertGreater(metrics['ENTROPY'], 0.90)

            # Ignite should fail
            # We need to mock subprocess so ignite doesn't actually run cargo
            with patch('subprocess.Popen'):
                 with self.assertRaisesRegex(SystemError, "KERNEL PANIC"):
                    self.adapter.ignite()
        print("Veto Logic: PASS")

    def test_mock_kernel_syntax(self):
        """Ensure Mock Kernel is valid Rust."""
        print("\nVerifying Mock Kernel Syntax...")
        result = subprocess.run(
            ["cargo", "check"],
            cwd="core/mock_kernel",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, "Mock Kernel failed syntax check")
        print("Mock Kernel Syntax: PASS")

    def test_bridge_syntax(self):
        """Ensure Rust Bridge is valid Rust."""
        print("\nVerifying Rust Bridge Syntax...")
        result = subprocess.run(
            ["cargo", "check"],
            cwd="bridge-rust",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(result.stderr)
        self.assertEqual(result.returncode, 0, "Rust Bridge failed syntax check")
        print("Rust Bridge Syntax: PASS")

if __name__ == '__main__':
    unittest.main()
