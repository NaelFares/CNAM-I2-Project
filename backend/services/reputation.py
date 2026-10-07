"""Paliers de reputation conducteur/passager.

Fonction pure, volontairement isolee du reste : elle ne lit ni la base ni
aucun modele, seulement deux nombres. Les deux sources qui l'alimenteront
n'existent pas encore dans le projet :

  - `rides_count` viendra des courses effectivement realisees, c'est-a-dire
    de la table de reservation en cours de developpement par ailleurs ;
  - `rating_avg` viendra de la notation, reportee tant que cette table n'est
    pas connue.

Tant que ces deux sources manquent, ce module n'est branche nulle part : rien
ne l'appelle dans l'API, et aucun badge n'est affiche. Le jour ou les courses
et les notes existent, il suffit de lui passer les deux valeurs -- aucune
decision sur le schema de reservation n'est prise ici, ce qui est justement
le but.
"""

from __future__ import annotations

from typing import NamedTuple, Optional


class Tier(NamedTuple):
    """Un palier : son identifiant technique, son libelle et ses seuils."""

    key: str
    label: str
    min_rides: int
    min_rating: float


# Du plus exigeant au moins exigeant : le premier palier atteint gagne.
TIERS: tuple[Tier, ...] = (
    Tier("expert", "Expérimenté", min_rides=20, min_rating=4.5),
    Tier("confirmed", "Confirmé", min_rides=5, min_rating=4.0),
    Tier("newcomer", "Nouveau", min_rides=0, min_rating=0.0),
)

DEFAULT_TIER = TIERS[-1]


def compute_tier(rides_count: int, rating_avg: Optional[float]) -> Tier:
    """Retourne le palier correspondant a un nombre de courses et une moyenne.

    `rating_avg` vaut None tant qu'aucune note n'a ete recue : l'utilisateur
    reste alors au palier de depart, quel que soit son nombre de courses. Un
    profil tres actif mais jamais note ne doit pas heriter d'un palier eleve
    par defaut -- c'est la note qui distingue les paliers, pas le volume seul.
    """
    if rating_avg is None:
        return DEFAULT_TIER

    for tier in TIERS:
        if rides_count >= tier.min_rides and rating_avg >= tier.min_rating:
            return tier
    return DEFAULT_TIER
