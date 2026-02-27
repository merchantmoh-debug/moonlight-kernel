import unittest
from unittest.mock import MagicMock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "bridge-python"))

# Mock rich before import
class MockRich:
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name): return MagicMock()

sys.modules['rich'] = MagicMock()
sys.modules['rich.live'] = MagicMock()
sys.modules['rich.layout'] = MagicMock()
sys.modules['rich.panel'] = MagicMock()
sys.modules['rich.align'] = MagicMock()
sys.modules['rich.table'] = MagicMock()
sys.modules['rich.console'] = MagicMock()
sys.modules['rich.text'] = MagicMock()

from dashboard import Dashboard

class TestDashboard(unittest.TestCase):
    def test_render(self):
        """Test that the dashboard renders without crashing."""
        gate = MagicMock()
        gate.analyze.return_value = {"ENTROPY": 0.5, "URGENCY": 0.5, "THREAT": 0.1, "DELTA": 0.0}

        dash = Dashboard(gate)
        # Update logs to ensure kinetic graph has data
        dash.update_logs("BENCHMARK_DATA: vectors_sec=10000, mb_sec=30")

        layout = dash.get_renderable()
        self.assertIsNotNone(layout)

if __name__ == '__main__':
    unittest.main()
