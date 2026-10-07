"""Shared API constants and lightweight domain helpers."""

ROLE_VALUES = {"driver", "passenger"}

MIN_CAR_SEATS = 1
MAX_CAR_SEATS = 4

# Styles musicaux proposes au profil. Liste fermee : elle sert a valider les
# valeurs recues, et les libelles d'affichage vivent cote frontend
# (frontend/src/lib/preferences.js) -- les deux doivent rester alignees.
MUSIC_GENRE_VALUES = (
    "pop",
    "rap",
    "rnb",
    "shatta",
    "latino",
    "reggae",
    "afrobeat",
    "rock",
    "metal",
    "electro",
    "jazz",
    "classique",
    "variete_francaise",
    "kpop",
    "soul_funk",
    "country",
)

# Au-dela, la selection n'informe plus personne : cocher douze styles revient
# a n'en cocher aucun.
MAX_MUSIC_GENRES = 5


def clean_music_genres(genres: list[str]) -> list[str]:
    """Ecarte les valeurs inconnues et les doublons, en gardant l'ordre recu.

    Un style retire du catalogue ne doit pas faire echouer la sauvegarde d'un
    profil qui le portait encore : on l'ignore silencieusement plutot que de
    renvoyer une erreur que l'utilisateur ne peut pas corriger.

    Vit ici plutot que dans les schemas Pydantic pour rester a cote du
    catalogue qu'elle valide, et testable sans dependance tierce.
    """
    seen: list[str] = []
    for genre in genres:
        if genre in MUSIC_GENRE_VALUES and genre not in seen:
            seen.append(genre)
    return seen[:MAX_MUSIC_GENRES]

SESSION_COOKIE_NAME = "covoit_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30

MIN_TIME_TOLERANCE = 5
MAX_TIME_TOLERANCE = 60

PREVIEW_CACHE_TTL_SECONDS = 60 * 15
