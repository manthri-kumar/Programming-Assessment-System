import unittest

from backend.scoring import CoreScore, classify, legacy_originality_score, legacy_structure_score, weighted_test_score


class ScoringTests(unittest.TestCase):
    def test_legacy_structure_zero_reference_feature(self):
        self.assertEqual(legacy_structure_score({"lines": 0}, {"lines": 0}), 100)
        self.assertEqual(legacy_structure_score({"lines": 0}, {"lines": 1}), 0)

    def test_legacy_similarity_and_weighted_tests(self):
        self.assertEqual(legacy_originality_score("same", "same"), 0)
        self.assertEqual(weighted_test_score(2, 4), 50)

    def test_core_weighting_and_boundaries(self):
        score = CoreScore(80, 100, 50, 40)
        self.assertEqual(score.total, 74)
        self.assertEqual(score.category, "Average")
        self.assertEqual([classify(v) for v in (49.999, 50, 74.999, 75)], ["Poor", "Average", "Average", "Good"])

    def test_component_bounds_are_enforced(self):
        with self.assertRaises(ValueError):
            CoreScore(101, 100, 100, 100)


if __name__ == "__main__":
    unittest.main()
