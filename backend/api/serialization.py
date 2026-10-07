"""Conversion des modeles vers leurs DTO d'API.

`UserDTO` n'expose pas le nom de fichier de la photo mais son URL publique :
c'est le seul champ derive du modele, et le construire ici evite de le
recalculer dans chaque route.
"""

from __future__ import annotations

from backend.models.user import User
from backend.services.photo_storage import build_photo_url

from backend.api.schemas import UserDTO


def user_to_dto(user: User) -> UserDTO:
    return UserDTO(**user.to_dict(), photo_url=build_photo_url(user.photo_filename))
