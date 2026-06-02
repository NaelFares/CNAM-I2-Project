# AI Planning Import - Documentation Technique

Ce dossier implémente l'import CSV assisté par IA du service de planning.

Objectif : convertir des colonnes CSV inconnues vers le format événement interne :
- `title`
- `start_time`
- `end_time`
- `location`
- `description`

## 1. Vue d'ensemble

Flux global :
1. Lecture CSV (encodage + séparateur auto).
2. Construction d'un échantillon JSON minimal (`headers` + `sample_rows`).
3. Appel au fournisseur IA (Ollama local ou Groq cloud) pour proposer un mapping.
4. Validation / reconstruction des événements sur tout le fichier.
5. Deuxième tentative IA si la première échoue.
6. Score de confiance final.

Code principal : `parser.py` (`CsvAiPlanningParser.parse`).
Fournisseurs IA : `providers/ollama.py` et `providers/groq.py`.

## 2. Ressources du dossier

- `parser.py` : orchestration complète (lecture CSV → appel IA → événements).
- `providers/__init__.py` : factory `get_provider()`, utilitaire `parse_json_response`.
- `providers/ollama.py` : fournisseur local via Ollama.
- `providers/groq.py` : fournisseur cloud via API Groq (gratuit, recommandé).
- `prompts/system_prompt.txt` : rôle et contraintes du modèle.
- `prompts/mapping_prompt_template.txt` : template du prompt utilisateur.
- `schemas/mapping_response.schema.json` : contrat JSON de sortie du modèle.
- `tests/test_mapping_contract.py` : vérifie les champs obligatoires du schéma.
- `debug/debug_csv_ai_mapping.py` : script de supervision pas à pas.
- `debug/benchmark_ai_models_ollama_local.py` : benchmark comparatif des modèles Ollama.

## 3. Etapes détaillées avec exemples JSON

### Etape A - Echantillon envoyé au modèle

```json
{
  "headers": ["Objet", "Debut", "Debut.1", "Fin", "Fin.1", "Description", "Emplacement"],
  "sample_rows": [
    {
      "Objet": "NSY102 - Cour magistral",
      "Debut": "03/11/2025",
      "Debut.1": "09:00:00",
      "Fin": "03/11/2025",
      "Fin.1": "12:30:00",
      "Description": "NSY102 : ...",
      "Emplacement": "Salle 321"
    }
  ]
}
```

### Etape B - Réponse attendue du modèle (JSON strict)

```json
{
  "summary": "Mapping CSV vers planning",
  "overall_confidence": 0.95,
  "fields": {
    "title":       { "mode": "single",           "columns": ["Objet"],              "confidence": 0.99 },
    "start_time":  { "mode": "datetime_combine", "columns": ["Debut", "Debut.1"],   "confidence": 0.95 },
    "end_time":    { "mode": "datetime_combine", "columns": ["Fin",   "Fin.1"],     "confidence": 0.95 },
    "location":    { "mode": "single",           "columns": ["Emplacement"],        "confidence": 0.90 },
    "description": { "mode": "single",           "columns": ["Description"],        "confidence": 0.90 }
  }
}
```

### Etape C - Mapping résolu appliqué par le parser

Le parser corrige certains cas :
- `single` + plusieurs colonnes → garde la première.
- `datetime_combine` avec colonne dupliquée → résout la seconde (`.1`) si possible.

### Etape D - Evénements reconstruits

```json
[
  {
    "title": "NSY102 - Cour magistral",
    "start_time": "2025-11-03T09:00:00",
    "end_time": "2025-11-03T12:30:00",
    "location": "Salle 321",
    "description": "NSY102 : ..."
  }
]
```

## 4. Gestion des erreurs

- Réponse JSON invalide (Ollama uniquement) : tentative de réparation via un second appel au modèle local.
- Echec de reconstruction : tentative IA #2 avec le message d'erreur de la tentative #1.
- Toujours en échec : erreur explicite `SCHEDULE_PREVIEW_FAILED`.

## 5. Paramètres importants

Depuis `.env` :

| Variable | Description |
|---|---|
| `AI_IMPORT_ENABLED` | Active ou désactive le workflow IA |
| `AI_IMPORT_PROVIDER` | `groq` (recommandé) ou `ollama` (local) |
| `AI_IMPORT_MODEL` | Modèle à utiliser (`llama-3.1-8b-instant` pour Groq, `qwen2.5:0.5b-instruct` pour Ollama) |
| `AI_IMPORT_CONFIDENCE_THRESHOLD` | Seuil en dessous duquel une revue manuelle est demandée |
| `GROQ_API_KEY` | Clé API Groq (gratuite sur console.groq.com) — requis si `AI_IMPORT_PROVIDER=groq` |
| `OLLAMA_BASE_URL` | URL de l'instance Ollama — requis si `AI_IMPORT_PROVIDER=ollama` |
| `OLLAMA_REQUEST_TIMEOUT_S` | Timeout Ollama (300s recommandé : le premier chargement GPU peut être long) |

## 6. Supervision / debug

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv
```

Le script affiche : colonnes lues, prompt envoyé, mapping reçu, mapping résolu, preview des événements reconstruits.

## 7. Limites connues

- Les caractères corrompus dans le CSV (`ï¿½`) ne sont pas récupérables.
- En mode Ollama, les petits modèles (0.5B) sont moins stables sur JSON strict → préférer Groq.
- La qualité du mapping dépend de la qualité de la première ligne d'exemple.
