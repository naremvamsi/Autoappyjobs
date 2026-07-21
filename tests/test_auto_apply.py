import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from auto_apply import get_answer_for_body, should_launch_headless


class TestAutoApplyHelpers(unittest.TestCase):
    def test_returns_answer_for_sre(self):
        self.assertEqual(get_answer_for_body("Please share your sre experience"), "5")

    def test_returns_answer_for_total_experience(self):
        self.assertEqual(get_answer_for_body("Mention total experience"), "9.8")

    def test_returns_none_when_no_keywords_match(self):
        self.assertIsNone(get_answer_for_body("Some unrelated question"))

    def test_launches_headless_in_ci(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            self.assertTrue(should_launch_headless())

    def test_launches_headed_locally(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(should_launch_headless())


if __name__ == "__main__":
    unittest.main()
