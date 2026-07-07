"""
Peuplement BD – insere des donnees de reference si elles n'existent pas encore.
Appele systematiquement par setup.run_startup() a chaque demarrage.
Toutes les requetes doivent etre idempotentes (INSERT ... WHERE NOT EXISTS).
"""
import logging

import psycopg2

from backend.core.config import config

logger = logging.getLogger(__name__)


def run_populate() -> None:
    conn = psycopg2.connect(config.DATABASE_URL, connect_timeout=5)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            pass  # Ajouter des fonctions _populate_xxx(cur) ici
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
