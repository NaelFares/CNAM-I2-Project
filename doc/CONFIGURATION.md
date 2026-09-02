# Configuration

Ce projet utilise un fichier `.env` a la racine comme source de verite.

## Variables obligatoires

- `APP_NAME`
- `APP_ENV`
- `STORAGE_SECRET`
- `DATABASE_URL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `FRONTEND_PORT`
- `BACKEND_PORT`
- `VITE_API_URL`
- `AI_IMPORT_ENABLED`
- `AI_IMPORT_CONFIDENCE_THRESHOLD`
- `GROQ_MODEL`
- `OLLAMA_MODEL`

## Variables metier (recommandees)

- `CAMPUS_NAME`
- `CAMPUS_LAT`
- `CAMPUS_LON`
- `DEFAULT_ZOOM`
- `DEFAULT_TIME_TOLERANCE_MIN`
- `MAX_DISTANCE_KM`
- `MIN_MATCH_SCORE`
- `MAX_FILE_SIZE_MB`
- `OLLAMA_KEEP_ALIVE`
- `OLLAMA_PORT`

## Notes

- `docker/docker-compose.groq.yml` décrit la stack complète avec Groq et injecte `GROQ_MODEL`.
- `docker/docker-compose.ollama.yml` décrit la stack complète avec Ollama et injecte `OLLAMA_MODEL`.
- `AI_IMPORT_PROVIDER` et `AI_IMPORT_MODEL` sont des variables runtime injectees par Compose, pas des choix a renseigner dans `.env`.
- `VITE_API_URL` est injecte au build du frontend.
- `OLLAMA_BASE_URL` doit rester `http://ia-services:11434` pour la communication inter-conteneurs.
- Pour un autre host, ajuster `VITE_API_URL` et CORS backend.

