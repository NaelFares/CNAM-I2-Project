import json
from pathlib import Path
import unittest


class TestMappingSchema(unittest.TestCase):
    def test_schema_has_required_fields(self):
        schema_path = Path("backend/services/planning_import_services/csv_ai/schemas/mapping_response.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = schema["properties"]["fields"]["required"]
        self.assertEqual(required, ["title", "start_time", "end_time", "location", "description"])


if __name__ == "__main__":
    unittest.main()
