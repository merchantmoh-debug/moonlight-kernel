import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure bridge-python is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

import adapter
from adapter import SignalGate

class TestSignalGateEnhanced(unittest.TestCase):
    def test_derivative_spike_veto(self):
        """Verify that a sudden 60% CPU spike triggers a THREAT escalation."""
        with patch.object(adapter, 'psutil') as mock_psutil:
            mock_psutil.cpu_percent.side_effect = [10.0, 70.0] # 10% -> 70% (Delta 0.6)
            mock_psutil.virtual_memory.return_value.percent = 20.0

            gate = SignalGate()

            # Initial baseline
            m1 = gate.analyze()
            self.assertAlmostEqual(m1['ENTROPY'], 0.1)
            self.assertAlmostEqual(m1['DELTA'], 0.1) # First reading delta from 0

            # Spike
            m2 = gate.analyze()
            self.assertAlmostEqual(m2['ENTROPY'], 0.7)
            self.assertAlmostEqual(m2['DELTA'], 0.6)

            # Threat should be escalated to at least 0.9 (Critical)
            self.assertGreaterEqual(m2['THREAT'], 0.9)

            # Veto should trigger even in non-strict mode because 0.9 > 0.8
            # Wait, default limit in my code: if strict: 0.7 else 0.95
            # Ah, I set limit to 0.95 for non-strict.
            # So 0.9 might barely pass non-strict, but fail strict.

            veto, reason = gate.check_veto(m2, strict=True)
            self.assertTrue(veto)
            self.assertIn("Operational Risk Critical", reason)

if __name__ == '__main__':
    unittest.main()
