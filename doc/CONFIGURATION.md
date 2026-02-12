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

## Variables metier (recommandees)

- `CAMPUS_NAME`
- `CAMPUS_LAT`
- `CAMPUS_LON`
- `DEFAULT_ZOOM`
- `DEFAULT_TIME_TOLERANCE_MIN`
- `MAX_DISTANCE_KM`
- `MIN_MATCH_SCORE`
- `MAX_FILE_SIZE_MB`

## Notes

- `docker-compose.yml` lit `.env` via `env_file` et substitutions `${...}`.
- `VITE_API_URL` est injecte au build du frontend.
- Pour un autre host, ajuster `VITE_API_URL` et CORS backend.

