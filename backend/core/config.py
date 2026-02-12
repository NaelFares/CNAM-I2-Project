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

    # Upload
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))

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
