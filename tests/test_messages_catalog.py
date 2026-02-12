import unittest

from backend.messages import get_message


class MessageCatalogTests(unittest.TestCase):
    def test_known_code_with_format(self):
        msg = get_message("SCHEDULE_IMPORT_SUCCESS", count=3)
        self.assertIn("3", msg)

    def test_unknown_code_returns_default(self):
        msg = get_message("UNKNOWN_CODE")
        self.assertEqual(msg, "Une erreur est survenue.")


if __name__ == "__main__":
    unittest.main()
