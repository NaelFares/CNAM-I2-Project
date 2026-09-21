import importlib
import sys
import types
import unittest

# `backend.api.session` ne lit que STORAGE_SECRET : on neutralise la config le
# temps de l'import, pour ne pas dependre de python-dotenv ni d'un .env.
# Le module garde ensuite sa propre reference vers ce faux objet, donc on peut
# restaurer sys.modules aussitot — sans cette restauration, le faux module
# restait en place pour tous les tests importes apres celui-ci, qui echouaient
# alors sur "cannot import name ... (unknown location)".
_previous_config = sys.modules.get("backend.core.config")

fake_config_module = types.ModuleType("backend.core.config")
fake_config_module.config = types.SimpleNamespace(STORAGE_SECRET="test-secret")
sys.modules["backend.core.config"] = fake_config_module

session_module = importlib.import_module("backend.api.session")

if _previous_config is None:
    del sys.modules["backend.core.config"]
else:
    sys.modules["backend.core.config"] = _previous_config


class SessionTokenTests(unittest.TestCase):
    def test_create_and_parse_token(self):
        token = session_module.create_session_token(user_id=42, email="user@example.com", ttl_seconds=60)
        payload = session_module.parse_session_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.user_id, 42)
        self.assertEqual(payload.email, "user@example.com")

    def test_expired_token_returns_none(self):
        token = session_module.create_session_token(user_id=1, email="expired@example.com", ttl_seconds=-1)
        payload = session_module.parse_session_token(token)
        self.assertIsNone(payload)


if __name__ == "__main__":
    unittest.main()
