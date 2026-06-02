# Quickstart Equipe

## Prerequis

- Docker Desktop
- PowerShell (script de demarrage)

## 1) Configuration

- Copier `.env.example` vers `.env` si besoin
- Ajuster les variables (ports, DB, secrets)

## 2) Demarrage recommande (logs explicites)

```powershell
./scripts/start-local.ps1
```

Ce script:
- lance `docker compose up -d --build --remove-orphans`
- affiche les URLs frontend/backend/ia-services
- demarre Ollama en CPU par defaut
- utilise le GPU uniquement avec l'option explicite `-ForceGpu`
- affiche l'etat des conteneurs
- puis suit les logs en direct (`docker compose logs -f`)

Pour demarrer sans suivre les logs:

```powershell
./scripts/start-local.ps1 -NoLogs
```

Pour choisir le mode IA:

```powershell
./scripts/start-local.ps1 -ForceCpu
./scripts/start-local.ps1 -ForceGpu
```

### Variante sans rebuild d'images

```powershell
./scripts/start-local-no-build.ps1
```

Utilise ce script quand les images sont deja construites et que tu veux juste relancer rapidement.

## 3) Verification manuelle

- Frontend: `http://localhost:${FRONTEND_PORT}` (defaut 3000)
- API health: `http://localhost:${BACKEND_PORT}/health` (defaut 8000)
- Ollama: `http://localhost:${OLLAMA_PORT}` (defaut 11434)

## Commandes utiles

### Arreter

```bash
docker compose down
```

Ou via script:

```powershell
./scripts/stop-local.ps1
```

### Logs

```bash
docker compose logs -f
```

### Verifier le modele IA charge

```bash
docker compose exec ia-services ollama list
```

### Benchmarker les modeles IA CSV

Depuis le conteneur backend, avec le service IA demarre:

```bash
docker compose exec backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --pull
```

Modeles compares par defaut: `qwen2.5:0.5b-instruct`, `qwen3:0.6b`, `gemma3:1b`.

### Rebuild complet

```bash
docker compose down -v
docker compose up --build -d --remove-orphans
```

## Tests

### Backend

```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Frontend (dans un conteneur Node)

```bash
docker run --rm -v "${PWD}/frontend:/app" -w /app node:22-alpine sh -lc "npm install && npm run test"
```
