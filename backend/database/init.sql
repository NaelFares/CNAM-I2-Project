-- Schema initialisation – safe to run multiple times (idempotent)

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    email               TEXT UNIQUE NOT NULL,
    hashed_password     TEXT NOT NULL DEFAULT '',
    -- Places proposees aux passagers. NULL tant que l'utilisateur n'a pas
    -- renseigne de voiture : il peut alors chercher, mais pas proposer.
    car_seats           INTEGER,
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
ALTER TABLE users ADD COLUMN IF NOT EXISTS car_seats       INTEGER;

-- Places : 1 a 4, ou NULL quand l'utilisateur n'a pas de voiture. Le role
-- exclusif conducteur/passager a ete supprime : tout compte peut chercher un
-- trajet ET en proposer un. La migration des donnees se fait apres la
-- creation de la table rides (cf. "Fin des roles exclusifs" plus bas).
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_car_seats_check;
ALTER TABLE users ADD CONSTRAINT users_car_seats_check
    CHECK (car_seats IS NULL OR car_seats BETWEEN 1 AND 4);

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

-- Nature du trajet : offre (je prends ma voiture) ou recherche (je cherche
-- une voiture). Porte par le trajet lui-meme et non plus par un role
-- d'utilisateur : la meme personne peut conduire le lundi et chercher le
-- mercredi. Un trajet issu du planning est une recherche par defaut.
ALTER TABLE rides ADD COLUMN IF NOT EXISTS is_offer BOOLEAN NOT NULL DEFAULT FALSE;

-- Adresses lisibles du depart et de l'arrivee. Utiles surtout aux trajets
-- proposes a la main (hors emploi du temps), dont le depart et l'arrivee sont
-- libres ; vides pour les trajets generes depuis le planning, qui vont du
-- domicile a l'ecole du profil. Un trajet sans event_id est un trajet cree a
-- la main : il ne disparait pas quand on reimporte son emploi du temps.
ALTER TABLE rides ADD COLUMN IF NOT EXISTS start_address TEXT NOT NULL DEFAULT '';
ALTER TABLE rides ADD COLUMN IF NOT EXISTS end_address   TEXT NOT NULL DEFAULT '';

-- Fin des roles exclusifs (migration unique). Tant que la colonne role
-- existe, les trajets des conducteurs deviennent des offres -- leurs
-- reservations restent ainsi valides -- puis la colonne est supprimee.
-- Le bloc ne s'execute plus ensuite, et jamais sur une base neuve.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'role'
    ) THEN
        UPDATE rides r SET is_offer = TRUE
        FROM users u
        WHERE u.id = r.user_id AND u.role = 'driver';
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;
        ALTER TABLE users DROP COLUMN role;
    END IF;
END $$;

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

-- Realignement des bases creees par une premiere version de la branche de
-- suivi : leur ride_selections avait ete creee sans ON DELETE CASCADE, et le
-- CREATE TABLE IF NOT EXISTS ci-dessus ne corrige pas une table existante.
-- Sans cela, supprimer un trajet ou un utilisateur reserve echoue (ex. reset
-- du seed au demarrage). Inoffensif sur une base neuve.
ALTER TABLE ride_selections DROP CONSTRAINT IF EXISTS ride_selections_ride_id_fkey;
ALTER TABLE ride_selections ADD CONSTRAINT ride_selections_ride_id_fkey
    FOREIGN KEY (ride_id) REFERENCES rides(id) ON DELETE CASCADE;
ALTER TABLE ride_selections DROP CONSTRAINT IF EXISTS ride_selections_passenger_id_fkey;
ALTER TABLE ride_selections ADD CONSTRAINT ride_selections_passenger_id_fkey
    FOREIGN KEY (passenger_id) REFERENCES users(id) ON DELETE CASCADE;
-- Colonnes d'annulation de cette meme premiere version, remplacees depuis par
-- status = 'rejected'. cancelled_by portait une cle etrangere vers users qui
-- bloquerait elle aussi la suppression d'un compte.
ALTER TABLE ride_selections DROP COLUMN IF EXISTS cancelled_by;
ALTER TABLE ride_selections DROP COLUMN IF EXISTS cancelled_at;

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

-- Suivi du covoiturage : quatre confirmations independantes, horodatees.
-- NULL = etape pas encore confirmee. On stocke un instant plutot qu'un
-- booleen pour savoir QUAND chaque partie a confirme, et un statut unique
-- representerait mal deux confirmations qui arrivent dans un ordre libre.
-- Ces colonnes completent le flux de reservation (status pending/accepted/
-- rejected) : elles ne deviennent pertinentes qu'une fois le passager accepte.
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS driver_picked_up_at   TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS passenger_onboard_at  TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS driver_completed_at   TIMESTAMPTZ;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS passenger_arrived_at  TIMESTAMPTZ;

-- Ou monte et descend le passager, quand et a quel cout pour le conducteur.
-- Renseigne a la reservation, a partir de la correspondance calculee : le
-- conducteur le voit avant d'accepter, et le matching additionne les detours
-- des passagers deja acceptes. NULL pour les reservations plus anciennes.
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS pickup_lat    DOUBLE PRECISION;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS pickup_lon    DOUBLE PRECISION;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS dropoff_lat   DOUBLE PRECISION;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS dropoff_lon   DOUBLE PRECISION;
-- Heure de depose (aller) ou de prise en charge (retour), "HH:MM".
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS passage_time  TEXT;
ALTER TABLE ride_selections ADD COLUMN IF NOT EXISTS detour_min    REAL;

-- RIDE_RATINGS
-- Notation d'une course terminee. Une note porte sur une reservation precise
-- (le couple conducteur/passager d'un trajet donne), pas sur un utilisateur
-- en general : c'est ce qui la rend verifiable -- on ne peut noter que
-- quelqu'un avec qui on a reellement roule.
--
-- Les deux parties se notent mutuellement, d'ou `rater_id` / `rated_id` :
-- deux lignes au maximum par reservation, une dans chaque sens.
CREATE TABLE IF NOT EXISTS ride_ratings (
    id                BIGSERIAL PRIMARY KEY,
    ride_selection_id BIGINT NOT NULL REFERENCES ride_selections(id) ON DELETE CASCADE,
    rater_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rated_id          INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score             SMALLINT NOT NULL,
    comment           TEXT NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Une seule note par personne et par course : la contrainte rend
    -- l'unicite impossible a contourner, meme par un double clic.
    UNIQUE (ride_selection_id, rater_id)
);

ALTER TABLE ride_ratings DROP CONSTRAINT IF EXISTS ride_ratings_score_check;
ALTER TABLE ride_ratings ADD CONSTRAINT ride_ratings_score_check
    CHECK (score BETWEEN 1 AND 5);

-- Personne ne se note soi-meme : sans cette contrainte, un utilisateur
-- pourrait gonfler sa propre moyenne en inserant des lignes.
ALTER TABLE ride_ratings DROP CONSTRAINT IF EXISTS ride_ratings_no_self_check;
ALTER TABLE ride_ratings ADD CONSTRAINT ride_ratings_no_self_check
    CHECK (rater_id <> rated_id);

-- Lecture typique : la moyenne et le nombre de notes recues par un profil.
CREATE INDEX IF NOT EXISTS idx_ride_ratings_rated ON ride_ratings(rated_id);
