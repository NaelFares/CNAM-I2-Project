# Technical Docs Index

## Actives

- `doc/ARCHITECTURE.md`: architecture, roles, flux runtime + mermaid
- `doc/CONFIGURATION.md`: variables d'environnement et politique de config
- `doc/DATABASE_SCHEMA.md`: schema et relations PostgreSQL
- `doc/MATCHING_ALGORITHM.md`: algorithme de matching covoiturage (filtrage, score, detour ORS)
- `doc/UI_VALIDATION_CHECKLIST.md`: checklist de validation UI

## Utilitaire equipe

- `scripts/start-local.ps1`: demarrage standard avec Groq cloud, sans Ollama
- `scripts/start-local-ollama.ps1`: demarrage explicite avec Ollama local en CPU
- `scripts/start-local-ollama-gpu.ps1`: demarrage explicite avec Ollama local en GPU
- `scripts/start-local-no-build.ps1`: demarrage Groq sans rebuild
- `scripts/stop-local.ps1`: arret de tous les services locaux Docker Compose
