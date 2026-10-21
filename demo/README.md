# Vidéo de démo Stud'Ride

Une capture réelle de l'app, pilotée par Playwright. Les annotations s'affichent pendant les pauses.

## Relancer l'enregistrement
1. Lancer la stack avec `scripts/start-local.ps1`.
2. Réinitialiser le seed. Le scénario envoie une demande, accepte une demande et note une course, il lui faut donc des données fraîches :
   `docker exec -e RESET_SEED=1 covoiturage-backend sh -c "cd /app && python -c 'from backend.database.populate import run_populate; run_populate()'"`
3. Dans `demo/`, lancer `npm install` puis `npm run record`. Le résultat est `output/studride-demo.mp4` (1080p, environ 5 min).
   - `FAST=1` lance une répétition rapide, sans pauses.
   - `HEADED=1` affiche le navigateur pendant l'enregistrement.

## Comptes (mot de passe `Test1234!`)
- Import CSV par IA : `etudiant34@studride-test.fr` (Maëlys, CNAM)
- Passagère : `etudiant01@studride-test.fr` (Léa, INSA)
- Conductrice : `etudiant30@studride-test.fr` (Julie, N7)

Les textes des annotations se modifient dans `record-demo.mjs` (appels à `annotate`), le style dans `overlay.js`.
