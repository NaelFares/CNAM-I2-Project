-- Schema initialisation – safe to run multiple times (idempotent)

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
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
