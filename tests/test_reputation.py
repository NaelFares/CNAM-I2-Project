import unittest

from backend.services.reputation import TIERS, compute_tier, rides_to_next_tier


class TierThresholdTests(unittest.TestCase):
    """Debutant 0-19, Intermediaire 20-49, Experimente 50+."""

    def test_beginner_range(self):
        for count in (0, 1, 10, 19):
            self.assertEqual(compute_tier(count).key, "beginner", f"{count} courses")

    def test_intermediate_range(self):
        for count in (20, 35, 49):
            self.assertEqual(compute_tier(count).key, "intermediate", f"{count} courses")

    def test_expert_range(self):
        for count in (50, 100, 1000):
            self.assertEqual(compute_tier(count).key, "expert", f"{count} courses")

    def test_exact_boundaries(self):
        """Les seuils sont inclusifs : 20 courses suffisent pour passer."""
        self.assertEqual(compute_tier(19).key, "beginner")
        self.assertEqual(compute_tier(20).key, "intermediate")
        self.assertEqual(compute_tier(49).key, "intermediate")
        self.assertEqual(compute_tier(50).key, "expert")

    def test_labels(self):
        self.assertEqual(compute_tier(0).label, "Débutant")
        self.assertEqual(compute_tier(20).label, "Intermédiaire")
        self.assertEqual(compute_tier(50).label, "Expérimenté")


class RobustnessTests(unittest.TestCase):
    def test_negative_or_none_falls_back_to_first_tier(self):
        """Une valeur aberrante ne doit pas faire planter l'affichage."""
        self.assertEqual(compute_tier(-5).key, "beginner")
        self.assertEqual(compute_tier(None).key, "beginner")

    def test_rating_no_longer_influences_the_tier(self):
        """Le palier ne depend que du volume : la note est affichee a part."""
        self.assertEqual(compute_tier(50).key, "expert")


class NextTierTests(unittest.TestCase):
    def test_counts_down_to_next_threshold(self):
        self.assertEqual(rides_to_next_tier(0), 20)
        self.assertEqual(rides_to_next_tier(19), 1)
        self.assertEqual(rides_to_next_tier(20), 30)
        self.assertEqual(rides_to_next_tier(49), 1)

    def test_none_at_last_tier(self):
        """Plus rien a atteindre une fois Experimente."""
        self.assertIsNone(rides_to_next_tier(50))
        self.assertIsNone(rides_to_next_tier(500))


class TierDefinitionTests(unittest.TestCase):
    def test_tiers_are_sorted_from_most_demanding(self):
        """compute_tier parcourt dans l'ordre : l'ordre fait la logique."""
        thresholds = [tier.min_rides for tier in TIERS]
        self.assertEqual(thresholds, sorted(thresholds, reverse=True))

    def test_lowest_tier_starts_at_zero(self):
        self.assertEqual(TIERS[-1].min_rides, 0)


if __name__ == "__main__":
    unittest.main()
