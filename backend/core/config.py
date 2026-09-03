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

    # Campus et géographie
    CAMPUS_NAME = os.getenv("CAMPUS_NAME", "Campus Central")
    CAMPUS_LAT = float(os.getenv("CAMPUS_LAT", "48.8566"))
    CAMPUS_LON = float(os.getenv("CAMPUS_LON", "2.3522"))
    DEFAULT_ZOOM = int(os.getenv("DEFAULT_ZOOM", "12"))

    # Paramètres de matching
    DEFAULT_TIME_TOLERANCE_MIN = int(os.getenv("DEFAULT_TIME_TOLERANCE_MIN", "15"))
    MAX_DISTANCE_KM = float(os.getenv("MAX_DISTANCE_KM", "10.0"))
    MIN_MATCH_SCORE = int(os.getenv("MIN_MATCH_SCORE", "60"))
    # Temps de detour maximum accepte (minutes) pour aller recuperer le
    # passager par rapport au trajet direct du conducteur (voir matching.py).
    MAX_DETOUR_MIN = float(os.getenv("MAX_DETOUR_MIN", "12.0"))
    # Nombre max de candidats (par trajet conducteur) pour lesquels on calcule
    # le detour reel via ORS - borne le nombre d'appels au service de routing.
    MAX_DETOUR_CANDIDATES = int(os.getenv("MAX_DETOUR_CANDIDATES", "8"))

    # Routing (OpenRouteService)
    ORS_API_KEY = os.getenv("ORS_API_KEY", "")

    # Upload
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))

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
        """Vérifie si on est en mode développement"""
        return cls.APP_ENV == "development"

    @classmethod
    def get_campus_coords(cls) -> tuple[float, float]:
        """Retourne les coordonnées du campus"""
        return (cls.CAMPUS_LAT, cls.CAMPUS_LON)


# Instance globale de configuration
config = Config()
