# Checklist de validation manuelle UI

## Pages a verifier
- `/login`
- `/register`
- `/profile`
- `/schedule`
- `/rides`
- `/matches`

## Scenarios feedback
- Erreur de formulaire vide: message centre, lisible, fermable.
- Erreur de format email: message metier clair.
- Erreur tolerance horaire invalide: message metier clair.
- Success profile/schedule/rides/matches: message centre et coherent.

## Scenarios session
- Login avec email inconnu: redirection `/register` + email pre-rempli.
- Refresh sur page protegee avec cookies valides: pas de redirection `/login`.
- Logout puis refresh: retour `/login`.

## Scenarios donnees
- Import CSV/ICS invalide: message non technique.
- Generation trajets: ride types coherents (`to_campus`, `from_campus`).
- Recherche correspondances: pas d'erreur runtime, resultat ou message metier.

## Responsive
- Largeur mobile (<= 390px): callouts restent centres, texte wrap, bouton fermeture accessible.
- Largeur desktop: callouts centres avec max-width stable.

