# Quickstart Equipe

## Prerequis

- Docker Desktop
- PowerShell (script de demarrage)

## 1) Configuration

- Copier `.env.example` vers `.env` si besoin
- Ajuster les variables (ports, DB, secrets)

## 2) Demarrage recommande (logs explicites)

```powershell
./start-local.ps1
```

Ce script:
- lance `docker compose up -d --build --remove-orphans`
- affiche les URLs frontend/backend
- affiche l'etat des conteneurs

### Variante sans rebuild d'images

```powershell
./start-local-no-build.ps1
```

Utilise ce script quand les images sont deja construites et que tu veux juste relancer rapidement.

## 3) Verification manuelle

- Frontend: `http://localhost:${FRONTEND_PORT}` (defaut 3000)
- API health: `http://localhost:${BACKEND_PORT}/health` (defaut 8000)

## Commandes utiles

### Arreter

```bash
docker compose down
```

### Logs

```bash
docker compose logs -f
```

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
