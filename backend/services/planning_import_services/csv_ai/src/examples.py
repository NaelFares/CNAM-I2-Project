"""Examples of expected IA response for CSV mapping."""

EXAMPLE_MAPPING = {
    "summary": "Objet mappe vers title. Debut/Fin combines pour les datetime.",
    "overall_confidence": 0.88,
    "fields": {
        "title": {"mode": "single", "columns": ["Objet"], "confidence": 0.95},
        "start_time": {"mode": "datetime_combine", "columns": ["Debut", "Debut.1"], "confidence": 0.9},
        "end_time": {"mode": "datetime_combine", "columns": ["Fin", "Fin.1"], "confidence": 0.9},
        "location": {"mode": "single", "columns": ["Emplacement"], "confidence": 0.8},
        "description": {"mode": "single", "columns": ["Description"], "confidence": 0.7},
    },
}
