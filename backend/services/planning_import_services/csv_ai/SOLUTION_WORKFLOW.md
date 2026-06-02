# AI Planning Import - Documentation Technique

Ce dossier documente la solution d'import CSV basee sur IA (Ollama) utilisee par le service d'import planning.

Objectif: convertir des colonnes CSV inconnues vers le format evenement interne:
- `title`
- `start_time`
- `end_time`
- `location`
- `description`

## 1. Vue d'ensemble

Flux global:
1. Lecture CSV (encodage + separateur auto).
2. Construction d'un echantillon JSON minimal (`headers` + `sample_rows`).
3. Appel LLM pour proposer un mapping.
4. Validation/reconstruction des evenements sur tout le fichier.
5. Deuxieme tentative IA si la premiere echoue.
6. Score de confiance final.

Code principal: `backend/services/planning_import_services/csv_ai/parser.py` (`CsvAiPlanningParser.parse`).

## 2. Ressources du dossier

- `prompts/system_prompt.txt`: role et contraintes du modele.
- `prompts/mapping_prompt_template.txt`: template du prompt utilisateur.
- `schemas/mapping_response.schema.json`: contrat JSON de sortie du modele.
- `tests/test_mapping_contract.py`: verifie les champs obligatoires du schema.
- `debug/debug_csv_ai_mapping.py`: script de supervision pas a pas.
- `debug/benchmark_ai_models.py`: benchmark comparatif des modeles Ollama.

## 3. Etapes detaillees avec exemples JSON

### Etape A - Echantillon envoye au modele

Le parser envoie l'en-tete ainsi qu'une ligne de contenu, sous forme JSON compact:

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

### Etape B - Reponse attendue du modele (JSON strict)

```json
{
  "summary": "Mapping CSV vers planning",
  "overall_confidence": 0.95,
  "fields": {
    "title": { "mode": "single", "columns": ["Objet"], "confidence": 0.99 },
    "start_time": { "mode": "datetime_combine", "columns": ["Debut", "Debut.1"], "confidence": 0.95 },
    "end_time": { "mode": "datetime_combine", "columns": ["Fin", "Fin.1"], "confidence": 0.95 },
    "location": { "mode": "single", "columns": ["Emplacement"], "confidence": 0.9 },
    "description": { "mode": "single", "columns": ["Description"], "confidence": 0.9 }
  }
}
```

### Etape C - Mapping resolu applique par le parser

Le parser corrige certains cas:
- `single` + plusieurs colonnes -> garde la premiere.
- `datetime_combine` avec colonne dupliquee -> resout la seconde (`.1`) si possible.

### Etape D - Evenements reconstruits

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

Cas geres:
- Reponse JSON invalide du modele:
  - tentative de reparation JSON via un second appel IA.
- Echec de reconstruction:
  - tentative IA #2 avec message d'erreur de la tentative #1.
- Toujours en echec:
  - erreur explicite `SCHEDULE_PREVIEW_FAILED`.

## 5. Parametres importants

Depuis `.env`:
- `AI_IMPORT_ENABLED`
- `OLLAMA_BASE_URL`
- `AI_IMPORT_MODEL`
- `AI_IMPORT_CONFIDENCE_THRESHOLD`
- `OLLAMA_KEEP_ALIVE`
- `OLLAMA_REQUEST_TIMEOUT_S` (300s recommande: le premier chargement GPU peut etre long)

## 6. Supervision / debug

Commande de debug (dans conteneur backend):

```powershell
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv
```

Le script affiche:
- colonnes lues,
- payload exact envoye au LLM,
- reponse brute modele,
- mapping recu,
- mapping resolu,
- preview des evenements reconstruits.

## 7. Limites connues

- Les caracteres deja corrompus dans le CSV (`ï¿½`) ne sont pas recuperables.
- Les petits modeles (0.5B) sont plus rapides, mais moins stables sur JSON strict.
- La qualite du mapping depend de la qualite de la premiere ligne d'exemple.
