"""Note attribuee a l'issue d'une course terminee.

Une note porte toujours sur une reservation precise, jamais sur un
utilisateur en general : on ne peut noter que quelqu'un avec qui on a
reellement roule, et une seule fois par course. C'est ce qui distingue
cette notation d'un systeme d'avis libre.

Les deux parties se notent mutuellement, chacune de son cote : le passager
note le conducteur, le conducteur note le passager.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

MIN_SCORE = 1
MAX_SCORE = 5

# Longueur volontairement modeste : un commentaire de covoiturage tient en
# deux phrases, et une borne basse limite ce qu'il y a a moderer.
MAX_COMMENT_LENGTH = 500


@dataclass
class RideRating:
    """Une note donnee par un participant a l'autre."""

    id: Optional[int] = None
    ride_selection_id: int = 0
    rater_id: int = 0
    rated_id: int = 0
    score: int = 0
    comment: str = ""
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ride_selection_id": self.ride_selection_id,
            "rater_id": self.rater_id,
            "rated_id": self.rated_id,
            "score": self.score,
            "comment": self.comment,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RideRating":
        return cls(
            id=data.get("id"),
            ride_selection_id=data.get("ride_selection_id", 0),
            rater_id=data.get("rater_id", 0),
            rated_id=data.get("rated_id", 0),
            score=data.get("score", 0),
            comment=data.get("comment") or "",
            created_at=data.get("created_at"),
        )


@dataclass
class RatingSummary:
    """Reputation d'un utilisateur, agregee depuis les notes recues."""

    average: Optional[float] = None
    count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "RatingSummary":
        count = int(data.get("count") or 0)
        average = data.get("average")
        return cls(
            # Aucune note recue : on distingue "pas encore note" (None) de
            # "mal note" (une moyenne basse). compute_tier s'appuie dessus.
            average=round(float(average), 2) if count and average is not None else None,
            count=count,
        )
