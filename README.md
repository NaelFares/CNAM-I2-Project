# CovoitEtudiant

Application de covoiturage étudiant, basée sur l'emploi du temps.

## Objectif

Faciliter les trajets quotidiens entre étudiants en proposant des correspondances pertinentes selon les horaires de cours.

## Fonctionnalites principales

- Création de compte et gestion du profil
- Import d'emploi du temps (ICS/CSV)
- Visualisation du planning en calendrier hebdomadaire
- Génération des trajets à partir des cours
- Recherche de correspondances entre étudiants

## Demarrage rapide

```powershell
./start-local.ps1
```

Démarrage sans rebuild d'images:

```powershell
./start-local-no-build.ps1
```

Accès local:

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Documentation

- Guide de lancement et commandes: `QUICKSTART.md`
- Documentation technique: `doc/TECHNICAL_INDEX.md`

## Contribution

1. Créer une branche depuis `main`
2. Faire des commits atomiques et explicites
3. Vérifier que l'application démarre correctement avant push

## Licence

Projet universitaire.
