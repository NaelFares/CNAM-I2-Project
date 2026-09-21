import unittest

from backend.services.reputation import compute_tier


class ReputationTierTests(unittest.TestCase):
    def test_never_rated_stays_newcomer(self):
        """Sans aucune note, le volume seul ne fait pas monter de palier."""
        self.assertEqual(compute_tier(0, None).key, "newcomer")
        self.assertEqual(compute_tier(100, None).key, "newcomer")

    def test_newcomer_below_thresholds(self):
        self.assertEqual(compute_tier(0, 5.0).key, "newcomer")
        self.assertEqual(compute_tier(4, 5.0).key, "newcomer")

    def test_confirmed_requires_both_criteria(self):
        self.assertEqual(compute_tier(5, 4.0).key, "confirmed")
        # Assez de courses mais note trop basse.
        self.assertEqual(compute_tier(50, 3.9).key, "newcomer")
        # Excellente note mais pas assez de courses.
        self.assertEqual(compute_tier(4, 5.0).key, "newcomer")

    def test_expert_at_exact_thresholds(self):
        self.assertEqual(compute_tier(20, 4.5).key, "expert")
        # Juste en dessous de chacun des deux seuils.
        self.assertEqual(compute_tier(19, 4.5).key, "confirmed")
        self.assertEqual(compute_tier(20, 4.49).key, "confirmed")

    def test_labels_are_exposed(self):
        self.assertEqual(compute_tier(20, 4.5).label, "Expérimenté")
        self.assertEqual(compute_tier(0, None).label, "Nouveau")


if __name__ == "__main__":
    unittest.main()
