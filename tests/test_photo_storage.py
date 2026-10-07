import sys
import types
import unittest

# Meme approche que tests/test_ai_config.py : le module de stockage tire
# backend.core.config, qui importe python-dotenv. On le stubbe pour que la
# suite reste lancable sans installer backend/requirements.txt.
if "dotenv" not in sys.modules:
    try:
        import dotenv  # noqa: F401
    except ModuleNotFoundError:
        stub = types.ModuleType("dotenv")
        stub.load_dotenv = lambda *a, **k: None
        sys.modules["dotenv"] = stub

from backend.services.photo_storage import (
    ALLOWED_CONTENT_TYPES,
    _build_filename,
    detect_content_type,
)

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 32
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"0" * 32


class DetectContentTypeTests(unittest.TestCase):
    def test_recognises_supported_formats(self):
        self.assertEqual(detect_content_type(JPEG), "image/jpeg")
        self.assertEqual(detect_content_type(PNG), "image/png")
        self.assertEqual(detect_content_type(WEBP), "image/webp")

    def test_rejects_non_image(self):
        self.assertIsNone(detect_content_type(b"<?php echo 1; ?>"))
        self.assertIsNone(detect_content_type(b""))

    def test_extension_alone_does_not_fool_detection(self):
        """Un script renomme en .png reste refuse : seul le contenu fait foi."""
        self.assertIsNone(detect_content_type(b"GIF89a" + b"0" * 32))

    def test_every_detected_type_is_allowed(self):
        for payload in (JPEG, PNG, WEBP):
            self.assertIn(detect_content_type(payload), ALLOWED_CONTENT_TYPES)


class BuildFilenameTests(unittest.TestCase):
    def test_filename_uses_detected_extension(self):
        self.assertTrue(_build_filename(7, "image/png").endswith(".png"))
        self.assertTrue(_build_filename(7, "image/jpeg").endswith(".jpg"))

    def test_filename_is_unpredictable(self):
        """Deux envois du meme utilisateur ne produisent pas le meme nom."""
        first = _build_filename(7, "image/png")
        second = _build_filename(7, "image/png")
        self.assertNotEqual(first, second)

    def test_filename_has_no_path_separator(self):
        name = _build_filename(7, "image/png")
        self.assertNotIn("/", name)
        self.assertNotIn("\\", name)
        self.assertNotIn("..", name)


if __name__ == "__main__":
    unittest.main()
