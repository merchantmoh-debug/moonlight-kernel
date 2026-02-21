import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock rich before it's imported by moonlight
mock_rich = MagicMock()
sys.modules["rich"] = mock_rich
sys.modules["rich.console"] = MagicMock()
sys.modules["rich.table"] = MagicMock()
sys.modules["rich.panel"] = MagicMock()
sys.modules["rich.progress"] = MagicMock()

# Add bridge-python to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "bridge-python"))

import moonlight

class TestCheckEnv(unittest.TestCase):
    @patch('moonlight.shutil.which')
    @patch('moonlight.console.print')
    def test_check_env_all_present(self, mock_print, mock_which):
        # Mock all tools found
        mock_which.side_effect = lambda x: f"/usr/bin/{x}"

        result = moonlight.check_env()

        self.assertTrue(result)
        # Verify console.print was called
        self.assertTrue(mock_print.called)

    @patch('moonlight.shutil.which')
    @patch('moonlight.console.print')
    def test_check_env_moon_missing(self, mock_print, mock_which):
        # Mock moon missing, others found
        def side_effect(arg):
            if arg == "moon":
                return None
            return f"/usr/bin/{arg}"
        mock_which.side_effect = side_effect

        result = moonlight.check_env()

        self.assertFalse(result)
        # Check if warning was printed
        found_warning = False
        for call in mock_print.call_args_list:
            args, _ = call
            if args and isinstance(args[0], str) and "WARNING: 'moon' CLI missing" in args[0]:
                found_warning = True
                break
        self.assertTrue(found_warning, "Warning about missing 'moon' not found in console output")

    @patch('moonlight.shutil.which')
    @patch('moonlight.sys.exit')
    @patch('moonlight.console.print')
    def test_check_env_essential_missing(self, mock_print, mock_exit, mock_which):
        # Mock cargo missing
        def side_effect(arg):
            if arg == "cargo":
                return None
            return f"/usr/bin/{arg}"
        mock_which.side_effect = side_effect

        moonlight.check_env()

        mock_exit.assert_called_with(1)
        # Check if critical error was printed
        found_critical = False
        for call in mock_print.call_args_list:
            args, _ = call
            if args and isinstance(args[0], str) and "CRITICAL: Essential tools missing" in args[0]:
                found_critical = True
                break
        self.assertTrue(found_critical, "Critical error about missing essential tools not found in console output")

if __name__ == '__main__':
    unittest.main()
