-- Schema initialisation – safe to run multiple times (idempotent)

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL DEFAULT '',
    role                TEXT NOT NULL DEFAULT 'both',
    start_address       TEXT DEFAULT '',
    start_lat           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    start_lon           DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    time_tolerance_min  INTEGER NOT NULL DEFAULT 15,
    school_address      TEXT DEFAULT '',
    school_lat          DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    school_lon          DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

-- Migrations : colonnes ajoutees apres le deploiement initial
-- Safe meme si la table users existait deja sans ces colonnes
ALTER TABLE users ADD COLUMN IF NOT EXISTS start_address   TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password TEXT NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS school_address  TEXT DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS school_lat      DOUBLE PRECISION DEFAULT 0.0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS school_lon      DOUBLE PRECISION DEFAULT 0.0;

-- EVENTS
CREATE TABLE IF NOT EXISTS events (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    title       TEXT NOT NULL,
    start_time  TIMESTAMP NOT NULL,
    end_time    TIMESTAMP NOT NULL,
    location    TEXT,
    description TEXT
);

-- RIDES
CREATE TABLE IF NOT EXISTS rides (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    event_id    INTEGER NOT NULL REFERENCES events(id),
    ride_type   TEXT NOT NULL,
    ride_time   TIMESTAMP NOT NULL,
    start_lat   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    start_lon   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    end_lat     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    end_lon     DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

-- Migration data : normalisation ride_type (no-op si deja applique)
UPDATE rides SET ride_type = 'to_campus'   WHERE ride_type = 'aller';
UPDATE rides SET ride_type = 'from_campus' WHERE ride_type = 'retour';

-- ROUTING CACHE
-- Resultats techniques reutilisables des calculs d'itineraires externes.
CREATE TABLE IF NOT EXISTS routing_cache (
    id              BIGSERIAL PRIMARY KEY,
    cache_key       TEXT UNIQUE NOT NULL,
    provider        TEXT NOT NULL DEFAULT 'ors',
    profile         TEXT NOT NULL DEFAULT 'driving-car',
    start_lat       DOUBLE PRECISION NOT NULL,
    start_lon       DOUBLE PRECISION NOT NULL,
    via_lat         DOUBLE PRECISION,
    via_lon         DOUBLE PRECISION,
    end_lat         DOUBLE PRECISION NOT NULL,
    end_lon         DOUBLE PRECISION NOT NULL,
    geometry        JSONB NOT NULL DEFAULT '[]'::jsonb,
    distance_m      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    duration_s      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    hit_count       INTEGER NOT NULL DEFAULT 0
);

-- Migration depuis la premiere version du cache : une route reste valide tant
-- que sa cle (coordonnees, profil, fournisseur et version) ne change pas.
DROP INDEX IF EXISTS idx_routing_cache_expires_at;
ALTER TABLE routing_cache DROP COLUMN IF EXISTS expires_at;
CREATE INDEX IF NOT EXISTS idx_routing_cache_last_used_at ON routing_cache(last_used_at);
