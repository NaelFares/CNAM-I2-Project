"""Orchestrateur de demarrage DB. Appeler run_startup() depuis main.py."""
import logging
import time
from pathlib import Path

import psycopg2
from psycopg2 import OperationalError

from backend.core.config import config

logger = logging.getLogger(__name__)

_INIT_SQL = Path(__file__).parent / "init.sql"
_MAX_RETRIES = 10
_RETRY_DELAY_S = 2


def run_startup() -> None:
    conn = _connect_with_retry()
    try:
        _run_schema_init(conn)
    finally:
        conn.close()
    _run_populate()
    logger.info("DB ready.")


def _connect_with_retry() -> psycopg2.extensions.connection:
    logger.info("Connecting to DB...")
    for attempt in range(_MAX_RETRIES):
        try:
            conn = psycopg2.connect(config.DATABASE_URL, connect_timeout=5)
            conn.autocommit = False
            logger.info("DB connection established.")
            return conn
        except OperationalError as exc:
            if attempt == _MAX_RETRIES - 1:
                logger.error("Could not connect to DB after %d attempts.", _MAX_RETRIES)
                raise
            logger.warning(
                "DB not ready (%d/%d): %s – retry in %ds...",
                attempt + 1,
                _MAX_RETRIES,
                exc,
                _RETRY_DELAY_S,
            )
            time.sleep(_RETRY_DELAY_S)


def _run_schema_init(conn: psycopg2.extensions.connection) -> None:
    logger.info("Running schema init...")
    sql = _INIT_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("Schema init complete.")


def _run_populate() -> None:
    logger.info("Running populate...")
    from backend.database.populate import run_populate
    run_populate()
    logger.info("Populate complete.")
