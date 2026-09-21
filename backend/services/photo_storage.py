"""Stockage des photos de profil sur le disque local.

Les fichiers vivent dans `config.PHOTO_STORAGE_DIR`, monte en volume Docker :
sans ce volume ils disparaitraient a chaque `docker compose up --build`.

La base ne stocke que le nom de fichier (cf. `users.photo_filename`), jamais
un chemin ni une URL : le repertoire et le prefixe d'URL restent des details
de configuration, modifiables sans migration de donnees.
"""

from __future__ import annotations

import logging
import secrets
from pathlib import Path
from typing import Optional

from backend.core.config import config

logger = logging.getLogger(__name__)

# Types acceptes, et extension canonique associee. On se fie au type MIME
# declare ET a la signature binaire du fichier : l'extension d'origine, elle,
# n'est jamais reutilisee (voir _build_filename).
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Signatures binaires (magic numbers) des formats acceptes. Un `Content-Type`
# est declare par le client : seul le contenu reel fait foi.
_MAGIC_NUMBERS: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)


def max_size_bytes() -> int:
    return config.MAX_PHOTO_SIZE_MB * 1024 * 1024


def build_photo_url(photo_filename: str) -> str:
    """URL publique d'une photo, ou chaine vide si l'utilisateur n'en a pas.

    Vit ici plutot que dans la couche API : le prefixe d'URL et le repertoire
    de stockage sont deux faces de la meme convention, et les garder ensemble
    evite qu'ils divergent.
    """
    if not photo_filename:
        return ""
    return f"{config.PHOTO_URL_PREFIX}/{photo_filename}"


def detect_content_type(content: bytes) -> Optional[str]:
    """Type reel du fichier d'apres sa signature binaire, ou None si inconnu.

    WebP se reconnait par un conteneur RIFF : "RIFF" suivi de 4 octets de
    taille, puis "WEBP".
    """
    for signature, content_type in _MAGIC_NUMBERS:
        if content.startswith(signature):
            return content_type
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "image/webp"
    return None


def _storage_dir() -> Path:
    directory = Path(config.PHOTO_STORAGE_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _build_filename(user_id: int, content_type: str) -> str:
    """Nom de fichier imprevisible, derive du type detecte.

    Le nom d'origine fourni par le client n'est jamais reutilise : il peut
    contenir des separateurs de chemin ou une extension mensongere. Le suffixe
    aleatoire evite par ailleurs qu'une photo remplacee reste accessible via
    une URL devinable, et casse le cache du navigateur a chaque changement.
    """
    extension = ALLOWED_CONTENT_TYPES[content_type]
    return f"user_{user_id}_{secrets.token_hex(8)}{extension}"


def save_photo(user_id: int, content: bytes, content_type: str) -> str:
    """Ecrit la photo et retourne son nom de fichier.

    Le type doit avoir ete valide en amont (cf. `detect_content_type`).
    """
    filename = _build_filename(user_id, content_type)
    (_storage_dir() / filename).write_bytes(content)
    return filename


def delete_photo(filename: str) -> None:
    """Supprime une photo si elle existe ; sans effet sinon.

    Tolerant a l'absence du fichier : une photo deja disparue du volume ne
    doit pas empecher d'en televerser une nouvelle.
    """
    if not filename:
        return
    # Defense en profondeur : on ne manipule que le dernier segment, pour
    # qu'une valeur corrompue en base ne puisse pas designer un autre dossier.
    safe_name = Path(filename).name
    try:
        (_storage_dir() / safe_name).unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Suppression de la photo %s impossible: %r", safe_name, exc)
