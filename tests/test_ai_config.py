import os
import sys
import types
from unittest.mock import patch
import unittest

try:
    import dotenv  # noqa: F401
except ModuleNotFoundError:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda: None
    sys.modules["dotenv"] = dotenv_stub

from backend.core.config import resolve_ai_import_config


class TestAiImportConfig(unittest.TestCase):
    def test_groq_uses_groq_model(self):
        environment = {
            "AI_IMPORT_PROVIDER": "groq",
            "GROQ_MODEL": "groq-test-model",
            "OLLAMA_MODEL": "ollama-test-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(resolve_ai_import_config(), ("groq", "groq-test-model"))

    def test_ollama_uses_ollama_model(self):
        environment = {
            "AI_IMPORT_PROVIDER": "ollama",
            "GROQ_MODEL": "groq-test-model",
            "OLLAMA_MODEL": "ollama-test-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(resolve_ai_import_config(), ("ollama", "ollama-test-model"))

    def test_runtime_model_override_has_priority(self):
        environment = {
            "AI_IMPORT_PROVIDER": "ollama",
            "OLLAMA_MODEL": "configured-model",
            "AI_IMPORT_MODEL": "runtime-model",
        }
        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(resolve_ai_import_config(), ("ollama", "runtime-model"))

    def test_invalid_provider_fails_fast(self):
        with patch.dict(os.environ, {"AI_IMPORT_PROVIDER": "typo"}, clear=True):
            with self.assertRaisesRegex(ValueError, "groq.*ollama"):
                resolve_ai_import_config()


if __name__ == "__main__":
    unittest.main()
