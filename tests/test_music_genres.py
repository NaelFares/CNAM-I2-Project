import sys
import types
import unittest

# Meme approche que tests/test_ai_config.py : on stubbe les dependances tierces
# absentes pour que la suite reste lancable sans backend/requirements.txt.
if "dotenv" not in sys.modules:
    try:
        import dotenv  # noqa: F401
    except ModuleNotFoundError:
        stub = types.ModuleType("dotenv")
        stub.load_dotenv = lambda *a, **k: None
        sys.modules["dotenv"] = stub

from backend.api.constants import MAX_MUSIC_GENRES, MUSIC_GENRE_VALUES, clean_music_genres as _clean
from backend.models.user import User


class WantsMusicTests(unittest.TestCase):
    def test_music_accepted(self):
        self.assertTrue(User(music_preference="avec").wants_music())
        self.assertTrue(User(music_preference="peu_importe").wants_music())

    def test_music_refused(self):
        self.assertFalse(User(music_preference="sans").wants_music())

    def test_genres_default_is_not_shared_between_instances(self):
        """Piege classique du dataclass : une liste mutable par defaut."""
        first, second = User(), User()
        first.music_genres.append("rap")
        self.assertEqual(second.music_genres, [])


class FromDictTests(unittest.TestCase):
    def test_missing_column_falls_back_to_empty_list(self):
        self.assertEqual(User.from_dict({"name": "Ancien compte"}).music_genres, [])

    def test_genres_are_copied_not_referenced(self):
        source = ["rap", "latino"]
        user = User.from_dict({"music_genres": source})
        user.music_genres.append("pop")
        self.assertEqual(source, ["rap", "latino"])


class CleanMusicGenresTests(unittest.TestCase):
    def test_keeps_known_values_in_order(self):
        self.assertEqual(_clean(["rap", "latino"]), ["rap", "latino"])

    def test_drops_unknown_values_silently(self):
        """Un style retire du catalogue ne doit pas bloquer la sauvegarde."""
        self.assertEqual(_clean(["rap", "genre_inconnu", "pop"]), ["rap", "pop"])

    def test_drops_duplicates(self):
        self.assertEqual(_clean(["rap", "rap", "pop"]), ["rap", "pop"])

    def test_caps_at_maximum(self):
        cleaned = _clean(list(MUSIC_GENRE_VALUES))
        self.assertEqual(len(cleaned), MAX_MUSIC_GENRES)

    def test_empty_stays_empty(self):
        self.assertEqual(_clean([]), [])

    def test_requested_genres_are_all_in_catalog(self):
        """Les styles demandes explicitement doivent exister."""
        for genre in ("pop", "rap", "shatta", "latino", "reggae"):
            self.assertIn(genre, MUSIC_GENRE_VALUES)


if __name__ == "__main__":
    unittest.main()
