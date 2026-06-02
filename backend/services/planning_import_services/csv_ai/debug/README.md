# Debug CSV IA

Ce dossier contient deux scripts à lancer depuis le conteneur `backend`.

**Mode Groq** (`AI_IMPORT_PROVIDER=groq`) : aucun service supplémentaire requis, les appels partent vers l'API cloud Groq.

**Mode Ollama** (`AI_IMPORT_PROVIDER=ollama`) : le service `ia-services` doit être démarré (`http://ia-services:11434`).

## Demarrer les services

Depuis la racine du projet, le plus simple est de lancer tous les services avec le script local:

```powershell
./scripts/start-local.ps1
```

Pour eviter le rebuild:

```powershell
./scripts/start-local.ps1 -NoBuild
```

Pour demarrer sans rester attache aux logs:

```powershell
./scripts/start-local.ps1 -NoLogs
```

Si vous voulez seulement les services utiles aux scripts IA:

```bash
docker compose up -d backend ia-services
```

## Benchmark des modeles

Compare des modèles Ollama locaux sur le même workflow que le backend : lecture CSV, prompt, appel Ollama, validation du mapping, reconstruction des événements et score de confiance. Réservé au mode `AI_IMPORT_PROVIDER=ollama`.

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --pull
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
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --repeats 1

# Choisir les modeles
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --models qwen2.5:0.5b-instruct qwen3:0.6b --pull

# Tester un autre CSV
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv --pull

# Sortie JSON uniquement
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --json
```

Sans `--pull`, le script echoue si un modele demande n'est pas deja present dans Ollama.

## Debug pas a pas du mapping CSV

Affiche les colonnes détectées, le prompt envoyé, le mapping reçu, le mapping résolu et les événements reconstruits. Fonctionne avec les deux fournisseurs (Ollama et Groq).

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv
```

Mode plus court:

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/debug_csv_ai_mapping.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv --quiet
```

## Verifier les modeles Ollama presents

```bash
docker compose exec ia-services ollama list
```

## Arreter apres debug

```bash
docker compose stop backend ia-services
```
