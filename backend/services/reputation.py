"""Palier d'experience d'un profil.

Le palier depend uniquement du nombre de courses effectivement realisees,
c'est-a-dire confirmees comme terminees par les deux parties. La note
moyenne est affichee a cote mais n'entre pas dans le calcul : elle dit la
qualite, le palier dit l'experience.

Un seul palier par profil, quel que soit le role : chaque course terminee
compte pour une, que la personne ait conduit ou ete passagere. Le detail
par role reste affiche a cote, a titre d'information.

Fonction pure, sans acces base ni dependance au reste : elle ne recoit
qu'un nombre.
"""

from __future__ import annotations

from typing import NamedTuple


class Tier(NamedTuple):
    """Un palier : identifiant technique, libelle affiche, seuil d'entree."""

    key: str
    label: str
    min_rides: int


# Du plus exigeant au moins exigeant : le premier palier atteint gagne.
TIERS: tuple[Tier, ...] = (
    Tier("expert", "Expérimenté", min_rides=50),
    Tier("intermediate", "Intermédiaire", min_rides=20),
    Tier("beginner", "Débutant", min_rides=0),
)

DEFAULT_TIER = TIERS[-1]


def compute_tier(rides_count: int) -> Tier:
    """Palier correspondant a un nombre de courses terminees.

    Debutant de 0 a 19 courses, Intermediaire de 20 a 49, Experimente a
    partir de 50.
    """
    count = max(0, int(rides_count or 0))
    for tier in TIERS:
        if count >= tier.min_rides:
            return tier
    return DEFAULT_TIER


def rides_to_next_tier(rides_count: int) -> int | None:
    """Courses restantes avant le palier suivant, ou None au dernier palier.

    Sert a afficher une progression lisible plutot qu'un palier opaque.
    """
    count = max(0, int(rides_count or 0))
    # TIERS est trie du plus exigeant au moins exigeant : on remonte pour
    # trouver le premier seuil encore devant nous.
    for tier in reversed(TIERS):
        if count < tier.min_rides:
            return tier.min_rides - count
    return None
