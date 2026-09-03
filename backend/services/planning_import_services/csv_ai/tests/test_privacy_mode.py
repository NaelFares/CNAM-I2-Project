import sys
import types
import unittest
from unittest.mock import Mock, patch

import pandas as pd

from backend.core.config import config
from backend.services.planning_import_services.csv_ai.parser import CsvAiPlanningParser
from backend.services.planning_import_services.csv_ai.providers.groq import GroqProvider


class TestCsvAiPrivacyMode(unittest.TestCase):
    def setUp(self):
        self.dataframe = pd.DataFrame(
            [{"Nom": "Jean Dupont", "Cours": "Architecture", "Debut": "03/09/2026 18:00"}]
        )

    def test_default_payload_contains_one_sample_row(self):
        payload = CsvAiPlanningParser._build_sample_payload(self.dataframe)

        self.assertEqual(payload["headers"], ["Nom", "Cours", "Debut"])
        self.assertEqual(payload["sample_rows"][0]["Nom"], "Jean Dupont")

    def test_privacy_payload_contains_headers_only(self):
        payload = CsvAiPlanningParser._build_sample_payload(self.dataframe, privacy_mode=True)

        self.assertEqual(payload, {
            "headers": ["Nom", "Cours", "Debut"],
            "sample_rows": [],
        })
        self.assertNotIn("Jean Dupont", str(payload))

    def test_header_only_payload_can_be_sent_to_provider(self):
        mapping = {
            "summary": "Mapping depuis les en-tetes.",
            "overall_confidence": 0.5,
            "fields": {},
        }
        provider = Mock()
        provider.call.return_value = mapping
        payload = CsvAiPlanningParser._build_sample_payload(self.dataframe, privacy_mode=True)

        with patch(
            "backend.services.planning_import_services.csv_ai.parser.get_provider",
            return_value=provider,
        ):
            result = CsvAiPlanningParser._request_ai_mapping(
                sample_payload=payload,
                available_columns=payload["headers"],
            )

        self.assertEqual(result, mapping)
        user_prompt = provider.call.call_args.args[1]
        self.assertIn('"sample_rows": []', user_prompt)
        self.assertNotIn("Jean Dupont", user_prompt)


class TestGroqStructuredOutput(unittest.TestCase):
    def test_provider_uses_strict_json_schema(self):
        completion = types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content='{"fields": {}}'))]
        )
        client = Mock()
        client.chat.completions.create.return_value = completion
        groq_module = types.ModuleType("groq")
        groq_module.Groq = Mock(return_value=client)
        schema = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

        with patch.dict(sys.modules, {"groq": groq_module}), patch.object(
            config,
            "AI_IMPORT_MODEL",
            "openai/gpt-oss-20b",
        ):
            GroqProvider().call("system", "user", schema)

        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["model"], "openai/gpt-oss-20b")
        self.assertEqual(request["response_format"]["type"], "json_schema")
        self.assertTrue(request["response_format"]["json_schema"]["strict"])
        self.assertEqual(request["response_format"]["json_schema"]["schema"], schema)


if __name__ == "__main__":
    unittest.main()
