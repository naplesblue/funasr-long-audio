import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from funasr_long_audio_safe.engine import ms_to_hms, sentences_to_json, sentences_to_text


class EngineSmokeTest(unittest.TestCase):
    def test_ms_to_hms(self):
        self.assertEqual(ms_to_hms(0), "[00:00:00]")
        self.assertEqual(ms_to_hms(3661000), "[01:01:01]")

    def test_sentence_formatters(self):
        data = [
            {"text": "hello", "start": 0, "end": 500},
            {"text": "world", "start": 1000, "end": 1500},
        ]
        text = sentences_to_text(data)
        self.assertIn("[00:00:00] hello", text)
        self.assertIn("[00:00:01] world", text)

        as_json = sentences_to_json(data)
        self.assertIn('"text": "hello"', as_json)


if __name__ == "__main__":
    unittest.main()
