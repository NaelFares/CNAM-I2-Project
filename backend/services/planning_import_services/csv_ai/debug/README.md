# Debug CSV IA

Ce dossier contient deux scripts a lancer depuis le conteneur `backend`.

Le service `ia-services` doit etre demarre, car les scripts appellent Ollama via `http://ia-services:11434`.

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

Compare les modeles sur le meme workflow que le backend: lecture CSV, prompt, appel Ollama, validation du mapping, reconstruction des evenements et score de confiance.

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models.py --pull
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
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models.py --repeats 1

# Choisir les modeles
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models.py --models qwen2.5:0.5b-instruct qwen3:0.6b --pull

# Tester un autre CSV
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models.py /app/backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv --pull

# Sortie JSON uniquement
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models.py --json
```

Sans `--pull`, le script echoue si un modele demande n'est pas deja present dans Ollama.

## Debug pas a pas du mapping CSV

Affiche les colonnes detectees, le payload envoye a Ollama, la reponse brute, le mapping resolu et les evenements reconstruits.

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
