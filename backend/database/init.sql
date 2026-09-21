-- Schema initialisation – safe to run multiple times (idempotent)

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL DEFAULT '',
    role                TEXT NOT NULL DEFAULT 'both',
    gender              TEXT NOT NULL DEFAULT 'autre',
    photo_filename      TEXT NOT NULL DEFAULT '',
    music_preference    TEXT NOT NULL DEFAULT 'peu_importe',
    music_genres        TEXT[] NOT NULL DEFAULT '{}',
    smoking_preference  TEXT NOT NULL DEFAULT 'peu_importe',
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
-- Sexe : les comptes anterieurs prennent le repli neutre 'autre'.
-- Le filtre "ladies only" n'est pas stocke ici : c'est une option ponctuelle
-- posee a chaque recherche (cf. MatchSearchRequest.ladies_only).
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender TEXT NOT NULL DEFAULT 'autre';

-- Preferences de trajet et photo de profil.
-- photo_filename ne stocke que le nom du fichier, jamais un chemin : les
-- fichiers vivent dans un volume Docker (cf. config.PHOTO_STORAGE_DIR) et
-- l'URL publique est reconstruite par l'API. Deplacer le stockage ne demande
-- donc aucune migration de donnees.
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_filename TEXT NOT NULL DEFAULT '';
ALTER TABLE users ADD COLUMN IF NOT EXISTS music_preference TEXT NOT NULL DEFAULT 'peu_importe';
-- Styles musicaux, uniquement pertinents quand music_preference vaut 'avec'
-- ou 'peu_importe'. Tableau : on en accepte plusieurs, la plupart des gens
-- n'ecoutant pas un seul genre. Vide = aucun style precise.
ALTER TABLE users ADD COLUMN IF NOT EXISTS music_genres TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS smoking_preference TEXT NOT NULL DEFAULT 'peu_importe';
-- car_seats a existe brievement puis a ete retire : on nettoie les bases de
-- developpement qui l'ont recue, IF EXISTS rendant l'instruction inoffensive
-- ailleurs.
ALTER TABLE users DROP COLUMN IF EXISTS car_seats;

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

-- RIDE_SELECTIONS
-- Table de reservation : un passager selectionne un trajet propose par un
-- conducteur. Sa definition reproduit volontairement le schema concu en
-- parallele pour la partie reservation, afin que les deux branches
-- convergent sans conflit -- CREATE TABLE IF NOT EXISTS rend l'instruction
-- inoffensive si l'autre version arrive en premier.
CREATE TABLE IF NOT EXISTS ride_selections (
    id            BIGSERIAL PRIMARY KEY,
    ride_id       INTEGER NOT NULL REFERENCES rides(id),
    passenger_id  INTEGER NOT NULL REFERENCES users(id),
    selected_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Un passager ne selectionne un trajet donne qu'une fois : sans cette
-- contrainte, un double-clic creerait deux reservations concurrentes dont
-- les suivis divergeraient.
CREATE UNIQUE INDEX IF NOT EXISTS ride_selections_ride_passenger_key
    ON ride_selections (ride_id, passenger_id);

-- Suivi du covoiturage : quatre confirmations independantes, horodatees.
-- NULL = etape pas encore confirmee. On stocke un instant plutot qu'un
-- booleen pour savoir QUAND chaque partie a confirme, et un statut unique
-- representerait mal deux confirmations qui arrivent dans un ordre libre.
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS driver_picked_up_at   TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS passenger_onboard_at  TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS driver_completed_at   TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS passenger_arrived_at  TIMESTAMPTZ;
-- Annulation : une reservation abandonnee ne doit pas rester eternellement
-- "en attente de prise en charge" dans les ecrans de suivi.
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS cancelled_at          TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS cancelled_by          INTEGER REFERENCES users(id);
