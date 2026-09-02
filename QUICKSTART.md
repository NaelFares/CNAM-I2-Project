# Quickstart équipe

## Prérequis

- Docker Desktop
- PowerShell

## 1. Configuration

- Copier `.env.example` vers `.env` si besoin.
- Renseigner `GROQ_API_KEY` pour le mode Groq.
- Ajuster les ports, la base de données et les modèles si nécessaire.

Le fournisseur IA n'est pas configuré dans `.env` : il est choisi explicitement par le script de démarrage.
Chaque script demande aussi si les 40 comptes de test doivent être régénérés avant de lancer la stack.

## 2. Choisir le mode IA

### Groq cloud — démarrage léger recommandé

```powershell
./scripts/start-local.ps1
```

Ce mode utilise `GROQ_MODEL` et ne télécharge ni l'image ni le modèle Ollama.

### Ollama local — CPU

```powershell
./scripts/start-local-ollama.ps1
```

Ce mode utilise `OLLAMA_MODEL`. Le premier lancement télécharge l'image Ollama et le modèle local.

### Ollama local — GPU

```powershell
./scripts/start-local-ollama-gpu.ps1
```

Le GPU doit être accessible depuis Docker. Le script CPU reste le choix compatible avec toutes les machines.

Pour démarrer sans suivre les logs, ajouter `-NoLogs`. Pour Groq sans reconstruire les images :

```powershell
./scripts/start-local-no-build.ps1
```

## 3. Accès local

- Frontend : `http://localhost:${FRONTEND_PORT}` — port 3000 par défaut
- API : `http://localhost:${BACKEND_PORT}` — port 8000 par défaut
- Health : `http://localhost:${BACKEND_PORT}/health`
- Ollama, uniquement avec les scripts Ollama : `http://localhost:${OLLAMA_PORT}` — port 11434 par défaut

## Commandes utiles

### Arrêter la stack active

```powershell
./scripts/stop-local.ps1
```

### Vérifier le modèle Ollama chargé

```powershell
docker exec covoiturage-ia-services ollama list
```

### Benchmarker les modèles Ollama

```powershell
docker exec covoiturage-backend python /app/backend/services/planning_import_services/csv_ai/debug/benchmark_ai_models_ollama_local.py --pull
```

Modèles comparés par défaut : `qwen2.5:0.5b-instruct`, `qwen3:0.6b`, `gemma3:1b`.

### Rebuild complet Groq

```powershell
docker compose -f docker/docker-compose.groq.yml down
docker compose -f docker/docker-compose.groq.yml up --build -d --remove-orphans
```

### Rebuild complet Ollama

```powershell
docker compose -f docker/docker-compose.ollama.yml down
docker compose -f docker/docker-compose.ollama.yml up --build -d --remove-orphans
```

## Tests

### Backend

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s backend/services/planning_import_services/csv_ai/tests -p "test_*.py"
```

### Frontend

```powershell
docker run --rm -v "${PWD}/frontend:/app" -w /app node:22-alpine sh -lc "npm install && npm run test"
```
