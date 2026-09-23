-- Schema initialisation – safe to run multiple times (idempotent)

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL DEFAULT '',
    role                TEXT NOT NULL DEFAULT 'passenger',
    car_seats           INTEGER,
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
ALTER TABLE users ADD COLUMN IF NOT EXISTS car_seats       INTEGER;

-- Migration vers deux roles exclusifs. Les anciens profils mixtes deviennent
-- passagers ; les conducteurs existants recoivent la capacite maximale.
UPDATE users SET role = 'passenger' WHERE role NOT IN ('driver', 'passenger');
UPDATE users SET car_seats = 4 WHERE role = 'driver' AND car_seats IS NULL;
UPDATE users SET car_seats = NULL WHERE role = 'passenger';
-- Conserve le scenario de demonstration historique : etudiant01 recherche
-- et etudiant07 propose le meme trajet.
UPDATE users
SET role = 'driver', car_seats = 4
WHERE email = 'etudiant07@studride-test.fr';
ALTER TABLE users ALTER COLUMN role SET DEFAULT 'passenger';
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE users ADD CONSTRAINT users_role_check
    CHECK (role IN ('driver', 'passenger'));
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_car_seats_check;
ALTER TABLE users ADD CONSTRAINT users_car_seats_check
    CHECK (
        (role = 'passenger' AND car_seats IS NULL)
        OR (role = 'driver' AND car_seats BETWEEN 1 AND 4)
    );

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
    event_id    INTEGER REFERENCES events(id) ON DELETE SET NULL,
    ride_type   TEXT NOT NULL,
    ride_time   TIMESTAMP NOT NULL,
    start_lat   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    start_lon   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    end_lat     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    end_lon     DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status      TEXT NOT NULL DEFAULT 'active',
    archived_at TIMESTAMPTZ
);

ALTER TABLE rides ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE rides ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;
ALTER TABLE rides ALTER COLUMN event_id DROP NOT NULL;
ALTER TABLE rides DROP CONSTRAINT IF EXISTS rides_event_id_fkey;
ALTER TABLE rides ADD CONSTRAINT rides_event_id_fkey
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE SET NULL;
ALTER TABLE rides DROP CONSTRAINT IF EXISTS rides_status_check;
ALTER TABLE rides ADD CONSTRAINT rides_status_check
    CHECK (status IN ('active', 'archived'));
CREATE INDEX IF NOT EXISTS idx_rides_status_time ON rides(status, ride_time);

-- Migration data : normalisation ride_type (no-op si deja applique)
UPDATE rides SET ride_type = 'to_campus'   WHERE ride_type = 'aller';
UPDATE rides SET ride_type = 'from_campus' WHERE ride_type = 'retour';

-- Choix d'un trajet conducteur par un passager connecte.
CREATE TABLE IF NOT EXISTS ride_selections (
    id              BIGSERIAL PRIMARY KEY,
    ride_id         INTEGER NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    passenger_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    selected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          TEXT NOT NULL DEFAULT 'accepted',
    UNIQUE (ride_id, passenger_id)
);
-- Les réservations déjà présentes restent confirmées ; les nouvelles demandes
-- sont créées explicitement avec le statut pending.
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'accepted';
ALTER TABLE ride_selections ALTER COLUMN status SET DEFAULT 'pending';
ALTER TABLE ride_selections DROP CONSTRAINT IF EXISTS ride_selections_status_check;
ALTER TABLE ride_selections ADD CONSTRAINT ride_selections_status_check
    CHECK (status IN ('pending', 'accepted', 'rejected'));
CREATE INDEX IF NOT EXISTS idx_ride_selections_passenger
    ON ride_selections(passenger_id);

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
