import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from funasr_long_audio_safe import cli


class CLIRoutingTest(unittest.TestCase):
    @patch("funasr_long_audio_safe.cli.engine.main")
    def test_worker_subcommand_adds_flag(self, mock_main):
        rc = cli.main(["worker", "--worker-max-jobs", "3"])
        self.assertEqual(rc, 0)
        mock_main.assert_called_once()

    @patch("funasr_long_audio_safe.cli.engine.main")
    def test_transcribe_passthrough(self, mock_main):
        rc = cli.main(["transcribe", "demo.mp3", "--format", "text"])
        self.assertEqual(rc, 0)
        mock_main.assert_called_once()


if __name__ == "__main__":
    unittest.main()
