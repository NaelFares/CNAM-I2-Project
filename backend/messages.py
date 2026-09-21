"""Central user-facing message catalog shared by API and clients."""

from __future__ import annotations


MESSAGE_CATALOG = {
    "AUTH_EMAIL_REQUIRED": "Merci de renseigner votre email.",
    "AUTH_EMAIL_INVALID": "Format d'email invalide.",
    "AUTH_UNKNOWN_EMAIL_REDIRECT": "Aucun compte trouve. Completez l'inscription pour continuer.",
    "REGISTER_REQUIRED_FIELDS": "Nom et email sont obligatoires.",
    "REGISTER_USER_EXISTING" : "L'utilisateur existe déjà. Veuillez vous connecter.",
    "PROFILE_REQUIRED_FIRST": "Vous devez d'abord creer votre profil.",
    "PROFILE_SAVE_SUCCESS": "Profil sauvegarde avec succes.",
    "PROFILE_SAVE_FAILED": "Impossible de sauvegarder le profil. Reessayez.",
    "PROFILE_ADDRESS_REQUIRED": "Merci de saisir une adresse avant la localisation.",
    "PROFILE_ADDRESS_NOT_FOUND": "Adresse introuvable. Essayez une adresse plus precise.",
    "PROFILE_ADDRESS_LOOKUP_FAILED": "La recherche d'adresse a echoue. Reessayez.",
    "PROFILE_ADDRESS_LOCATED": "Adresse localisee sur la carte.",
    "PROFILE_REVERSE_GEOCODE_FAILED": "Impossible de retrouver l'adresse pour ce point.",
    "PROFILE_MAP_COORDS_INVALID": "Coordonnees de carte invalides.",
    "PROFILE_PHOTO_EMPTY": "Le fichier envoye est vide.",
    "PROFILE_PHOTO_UNSUPPORTED": "Format d'image non supporte (JPEG, PNG ou WebP uniquement).",
    "PROFILE_PHOTO_TOO_LARGE": "L'image depasse la taille maximale de {max_mb} Mo.",
    "PROFILE_PHOTO_SAVE_FAILED": "Impossible d'enregistrer la photo. Reessayez.",
    "PROFILE_PHOTO_UPDATED": "Photo de profil mise a jour.",
    "PROFILE_PHOTO_DELETED": "Photo de profil supprimee.",
    "SCHEDULE_FILE_REQUIRED": "Merci de selectionner un fichier avant de valider.",
    "SCHEDULE_EMPTY_FILE": "Le fichier est vide ou illisible.",
    "SCHEDULE_UNSUPPORTED_FORMAT": "Format de fichier non supporte (ICS ou CSV uniquement).",
    "SCHEDULE_PREVIEW_SUCCESS": "{count} cours detectes - Verifiez puis confirmez l'import.",
    "SCHEDULE_PREVIEW_FAILED": "Impossible de lire le fichier. Verifiez son format. {reason}",
    "SCHEDULE_IMPORT_EMPTY": "Aucun evenement a importer.",
    "SCHEDULE_IMPORT_SUCCESS": "{count} cours importes avec succes !",
    "SCHEDULE_IMPORT_FAILED": "Impossible d'importer les evenements. Reessayez.",
    "RIDES_GENERATE_SUCCESS": "{count} trajets generes avec succes !",
    "RIDES_GENERATE_FAILED": "Impossible de generer les trajets. Reessayez.",
    "MATCHES_REQUIRED_RIDES": "Vous devez d'abord generer vos trajets.",
    "MATCHES_FOUND": "{count} correspondances trouvees !",
    "MATCHES_FIND_FAILED": "Impossible de rechercher des correspondances. Reessayez.",
    "MATCHES_LADIES_ONLY_FORBIDDEN": "L'option \"entre femmes\" est reservee aux utilisatrices.",
    "VALIDATION_TIME_TOLERANCE_INVALID": "La tolerance horaire doit etre un nombre entre 5 et 60.",
}


def get_message(code: str, **kwargs) -> str:
    template = MESSAGE_CATALOG.get(code, "Une erreur est survenue.")
    try:
        return template.format(**kwargs)
    except Exception:
        return template
