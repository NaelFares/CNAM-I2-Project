"""
Configuration centralisée de l'application.
Toutes les variables d'environnement sont chargées depuis .env
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class Config:
    """Classe de configuration centralisée"""

    # Application
    APP_NAME = os.getenv("APP_NAME", "CovoitEtudiant")
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
    MAX_ROUTE_DETOUR_KM = float(os.getenv("MAX_ROUTE_DETOUR_KM", "1.5"))

    # Routing (OpenRouteService)
    ORS_API_KEY = os.getenv("ORS_API_KEY", "")

    # Upload
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))

    # Import IA (CSV)
    AI_IMPORT_ENABLED = os.getenv("AI_IMPORT_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    AI_IMPORT_PROVIDER = os.getenv("AI_IMPORT_PROVIDER", "ollama")  # "ollama" | "groq"
    AI_IMPORT_MODEL = os.getenv("AI_IMPORT_MODEL", "qwen2.5:0.5b-instruct")
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
