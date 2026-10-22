"""
Configuration centralisée de l'application.
Toutes les variables d'environnement sont chargées depuis .env
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


def resolve_ai_import_config() -> tuple[str, str]:
    """Retourne un couple fournisseur/modele valide depuis l'environnement."""
    provider = os.getenv("AI_IMPORT_PROVIDER", "groq").strip().lower()
    if provider == "groq":
        default_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    elif provider == "ollama":
        default_model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b-instruct")
    else:
        raise ValueError("AI_IMPORT_PROVIDER doit valoir 'groq' ou 'ollama'.")

    return provider, os.getenv("AI_IMPORT_MODEL", default_model)


_RESOLVED_AI_IMPORT_PROVIDER, _RESOLVED_AI_IMPORT_MODEL = resolve_ai_import_config()


class Config:
    """Classe de configuration centralisée"""

    # Application
    APP_NAME = os.getenv("APP_NAME", "Stud'Ride")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_PORT = int(os.getenv("APP_PORT", "8501"))
    STORAGE_SECRET = os.getenv("STORAGE_SECRET", "covoiturage-secret-key-change-in-production")

    # Base de données
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://covoit:covoit_password@database:5432/covoiturage",
    )

    # Campus et géographie. Le campus par defaut sert de destination aux
    # comptes sans ecole renseignee : il doit rester dans la zone de la carte
    # OSRM (Toulouse), d'ou l'Universite Toulouse Capitole, en centre-ville.
    CAMPUS_NAME = os.getenv("CAMPUS_NAME", "Université Toulouse Capitole")
    CAMPUS_LAT = float(os.getenv("CAMPUS_LAT", "43.606136"))
    CAMPUS_LON = float(os.getenv("CAMPUS_LON", "1.438197"))
    DEFAULT_ZOOM = int(os.getenv("DEFAULT_ZOOM", "12"))

    # Paramètres de matching
    DEFAULT_TIME_TOLERANCE_MIN = int(os.getenv("DEFAULT_TIME_TOLERANCE_MIN", "15"))
    # Distance maximale (km) entre la route du conducteur et les points de
    # prise en charge et de depose du passager : au-dela, pas candidat.
    MAX_ROUTE_DISTANCE_KM = float(os.getenv("MAX_ROUTE_DISTANCE_KM", "2.0"))
    # Detour total maximum (minutes) quand plusieurs passagers partagent la
    # meme voiture : chacun reste sous MAX_DETOUR_MIN, leur somme sous ce seuil.
    MAX_TOTAL_DETOUR_MIN = float(os.getenv("MAX_TOTAL_DETOUR_MIN", "20.0"))
    # Deux trajets a moins de cet ecart (minutes) se chevauchent : on ne peut
    # pas etre engage sur les deux (deux voitures, ou conducteur et passager).
    SLOT_CONFLICT_MIN = int(os.getenv("SLOT_CONFLICT_MIN", "45"))
    # Temps de detour maximum accepte (minutes) pour aller recuperer le
    # passager par rapport au trajet direct du conducteur (voir matching.py).
    MAX_DETOUR_MIN = float(os.getenv("MAX_DETOUR_MIN", "12.0"))
    # Nombre max de candidats (par trajet de l'utilisateur courant) pour lesquels on calcule
    # le detour reel via OSRM - borne le nombre de calculs d'itineraire.
    MAX_DETOUR_CANDIDATES = int(os.getenv("MAX_DETOUR_CANDIDATES", "3"))

    # Routing : serveur OSRM local (service docker "osrm").
    OSRM_URL = os.getenv("OSRM_URL", "http://osrm:5000")

    # Upload
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))

    # Photos de profil : repertoire de stockage (monte en volume Docker, sinon
    # les photos disparaissent a chaque reconstruction d'image) et prefixe
    # d'URL publique sous lequel l'API les sert en statique.
    PHOTO_STORAGE_DIR = os.getenv("PHOTO_STORAGE_DIR", "/app/data/profile_photos")
    PHOTO_URL_PREFIX = "/media/profile-photos"
    MAX_PHOTO_SIZE_MB = int(os.getenv("MAX_PHOTO_SIZE_MB", "2"))

    # Import IA (CSV)
    AI_IMPORT_ENABLED = os.getenv("AI_IMPORT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    AI_IMPORT_PROVIDER = _RESOLVED_AI_IMPORT_PROVIDER
    AI_IMPORT_MODEL = _RESOLVED_AI_IMPORT_MODEL
    AI_IMPORT_CONFIDENCE_THRESHOLD = float(os.getenv("AI_IMPORT_CONFIDENCE_THRESHOLD", "0.80"))
    # Ollama
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ia-services:11434")
    OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "10m")
    OLLAMA_REQUEST_TIMEOUT_S = int(os.getenv("OLLAMA_REQUEST_TIMEOUT_S", "300"))
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    @classmethod
    def is_development(cls) -> bool:
        return cls.APP_ENV == "development"

    @classmethod
    def get_campus_coords(cls) -> tuple[float, float]:
        return (cls.CAMPUS_LAT, cls.CAMPUS_LON)

config = Config()
