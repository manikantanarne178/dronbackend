"""
Integration tests for AutoDCR REST API functions and models.
"""

import unittest
from app.autodcr.rule_loader import RuleLoader


class TestAPI(unittest.TestCase):

    def test_rules_loader(self):
        res = RuleLoader.load_rules_for_occupancy("Residential")
        self.assertEqual(res["zone"], "Residential")
        self.assertIn("ground_coverage", res["rules"])

    def test_commercial_rules_loader(self):
        res = RuleLoader.load_rules_for_occupancy("Commercial")
        self.assertEqual(res["zone"], "Commercial")
        self.assertIn("stp", res["rules"])


if __name__ == "__main__":
    unittest.main()
