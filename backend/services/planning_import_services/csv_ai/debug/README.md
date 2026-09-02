# Debug CSV IA

Ce dossier contient deux scripts à lancer depuis le conteneur `backend`.

**Mode Groq** (`start-local.ps1`) : aucun service supplémentaire requis, les appels partent vers l'API cloud Groq.

**Mode Ollama** (`start-local-ollama.ps1`) : le service `ia-services` est démarré sur `http://ia-services:11434`.

## Demarrer les services

Depuis la racine du projet, choisir explicitement le fournisseur:

```powershell
./scripts/start-local.ps1
./scripts/start-local-ollama.ps1
```

Pour eviter le rebuild:

```powershell
./scripts/start-local-no-build.ps1
./scripts/start-local-ollama.ps1 -NoBuild
```

Pour demarrer sans rester attache aux logs:

```powershell
./scripts/start-local.ps1 -NoLogs
./scripts/start-local-ollama.ps1 -NoLogs
```

## Benchmark des modeles

Compare des modèles Ollama locaux sur le même workflow que le backend : lecture CSV, prompt, appel Ollama, validation du mapping, reconstruction des événements et score de confiance. Réservé au démarrage `start-local-ollama.ps1`.

```bash
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --pull
```

Chaque execution ecrit aussi un rapport Markdown date dans:

```text
backend/services/planning_import_services/csv_ai/debug/benchmark_results/
```

Exemple:

```text
benchmark_results_2026-05-04.md
```

Modeles compares par defaut:

```text
qwen2.5:0.5b-instruct
qwen3:0.6b
gemma3:1b
```

Options utiles:

```bash
# Un seul passage par modele
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --repeats 1

# Choisir les modeles
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --models qwen2.5:0.5b-instruct qwen3:0.6b --pull

# Tester un autre CSV
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv --pull

# Sortie JSON uniquement
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --json
```

Sans `--pull`, le script echoue si un modele demande n'est pas deja present dans Ollama.

## Debug pas a pas du mapping CSV

Affiche les colonnes détectées, le prompt envoyé, le mapping reçu, le mapping résolu et les événements reconstruits. Fonctionne avec les deux fournisseurs (Ollama et Groq).

```bash
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv
```

Mode plus court:

```bash
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv --quiet
```

## Verifier les modeles Ollama presents

```bash
docker exec covoiturage-ia-services ollama list
```

## Arreter apres debug

```bash
./scripts/stop-local.ps1
```
