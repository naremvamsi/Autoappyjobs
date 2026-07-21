import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auto_apply import get_answer_for_body


class TestAutoApplyHelpers(unittest.TestCase):
    def test_returns_answer_for_sre(self):
        self.assertEqual(get_answer_for_body("Please share your sre experience"), "5")

    def test_returns_answer_for_total_experience(self):
        self.assertEqual(get_answer_for_body("Mention total experience"), "9.8")

    def test_returns_none_when_no_keywords_match(self):
        self.assertIsNone(get_answer_for_body("Some unrelated question"))


if __name__ == "__main__":
    unittest.main()
