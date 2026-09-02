"""
Peuplement BD – insere des donnees de reference si elles n'existent pas encore.
Appele systematiquement par setup.run_startup() a chaque demarrage.
Toutes les requetes doivent etre idempotentes (INSERT ... WHERE NOT EXISTS).
"""
import logging
import os
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from passlib.context import CryptContext

from backend.core.config import config
from backend.database.manager import db
from backend.models.event import Event
from backend.models.user import User
from backend.services.geocoding import geocoding_service

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOULOUSE_SCHOOLS = [
    ("INSA Toulouse", "135 Avenue de Rangueil, 31077 Toulouse"),
    ("ENSEEIHT (N7)", "2 Rue Charles Camichel, 31071 Toulouse"),
    ("IUT Blagnac", "1 Place Georges Brassens, 31703 Blagnac"),
    ("Université Toulouse Capitole", "2 Rue du Doyen Gabriel Marty, 31042 Toulouse"),
    ("Université Toulouse Jean Jaurès", "5 Allée Antonio Machado, 31100 Toulouse"),
    ("CNAM Occitanie Toulouse", "118 Route de Narbonne, 31062 Toulouse"),
]
SEED_PASSWORD = "Test1234!"
SEED_COUNT = 40
SEED_EMAIL_DOMAIN = "studride-test.fr"
ACCOUNTS_FILE = Path(__file__).parent / "seed_accounts.txt"

FIRST_NAMES = ["Camille", "Lucas", "Léa", "Hugo", "Manon", "Nathan", "Chloé", "Enzo", "Sarah", "Louis"]
LAST_NAMES = ["Martin", "Bernard", "Dubois", "Petit", "Durand", "Leroy", "Moreau", "Simon", "Laurent", "Roux"]

# Vraies rues réparties sur Toulouse, Blagnac et Colomiers — une par
# utilisateur de test (40 rues distinctes, une seule par personne), chacune
# vérifiée individuellement contre Nominatim avant d'être ajoutée ici.
# Géocodées une seule fois au premier démarrage (comme les écoles).
HOME_STREETS = [
    ("Rue Alsace-Lorraine", "31000 Toulouse"),
    ("Rue de Metz", "31000 Toulouse"),
    ("Avenue Jean Rieux", "31500 Toulouse"),
    ("Rue du Taur", "31000 Toulouse"),
    ("Rue Bayard", "31000 Toulouse"),
    ("Avenue de Muret", "31300 Toulouse"),
    ("Rue Pargaminières", "31000 Toulouse"),
    ("Boulevard de Strasbourg", "31000 Toulouse"),
    ("Avenue des Minimes", "31200 Toulouse"),
    ("Rue Riquet", "31000 Toulouse"),
    ("Rue Gambetta", "31000 Toulouse"),
    ("Rue Saint-Rome", "31000 Toulouse"),
    ("Rue de la Pomme", "31000 Toulouse"),
    ("Rue Ozenne", "31000 Toulouse"),
    ("Rue des Filatiers", "31000 Toulouse"),
    ("Rue Peyrolières", "31000 Toulouse"),
    ("Rue Boulbonne", "31000 Toulouse"),
    ("Rue de la Colombette", "31000 Toulouse"),
    ("Rue d'Aubuisson", "31000 Toulouse"),
    ("Boulevard de Bonrepos", "31000 Toulouse"),
    ("Rue des Tourneurs", "31000 Toulouse"),
    ("Rue Croix-Baragnon", "31000 Toulouse"),
    ("Rue Cujas", "31000 Toulouse"),
    ("Rue des Couteliers", "31000 Toulouse"),
    ("Rue Lafayette", "31000 Toulouse"),
    ("Rue du Vieux-Blagnac", "31700 Blagnac"),
    ("Rue Verlaine", "31700 Blagnac"),
    ("Avenue des Tilleuls", "31700 Blagnac"),
    ("Rue Toulouse Lautrec", "31700 Blagnac"),
    ("Place de Verdun", "31700 Blagnac"),
    ("Rue de la Poste", "31700 Blagnac"),
    ("Avenue du Général de Gaulle", "31700 Blagnac"),
    ("Rue de Purpan", "31700 Blagnac"),
    ("Rue de la République", "31700 Blagnac"),
    ("Allée Abel Boyer", "31770 Colomiers"),
    ("Allée de l'Adour", "31770 Colomiers"),
    ("Allée de l'Agly", "31770 Colomiers"),
    ("Rue de l'Oratoire", "31770 Colomiers"),
    ("Avenue de Colomiers", "31770 Colomiers"),
    ("Route de Toulouse", "31770 Colomiers"),
]


def run_populate() -> None:
    if not config.is_development():
        return

    if db.get_user_by_email(f"etudiant01@{SEED_EMAIL_DOMAIN}"):
        if _should_reset_seed():
            logger.info("Reinitialisation du seed de test demandee.")
            _delete_seed_users()
            created = _create_seed_users()
            logger.info(f"{created}/{SEED_COUNT} profils de test recrees.")
        else:
            logger.info("Seed de test conserve tel quel.")
    else:
        created = _create_seed_users()
        logger.info(f"{created}/{SEED_COUNT} profils de test crees.")

    _write_accounts_file()


def _should_reset_seed() -> bool:
    """Determine s'il faut regenerer le seed existant.

    - Si RESET_SEED est positionnee (ex. par les scripts start-local.ps1 et
      start-local-ollama.ps1, qui demandent dans le terminal hote avant de
      lancer Docker Compose, la question ne pouvant pas atteindre le conteneur),
      on l'utilise telle quelle.
    - Sinon, on retombe sur un prompt interactif local (lancement direct de
      uvicorn hors Docker, avec un vrai TTY).
    - En contexte non-interactif sans RESET_SEED (Docker sans -it, CI), on
      conserve l'existant par defaut plutot que de bloquer le demarrage."""
    env_value = os.getenv("RESET_SEED")
    if env_value is not None:
        return env_value.strip().lower() in ("1", "true", "o", "oui", "y", "yes")

    if not sys.stdin.isatty():
        return False
    try:
        answer = input(
            "\n[populate] Des donnees de test existent deja "
            f"(etudiant01..{SEED_COUNT:02d}@{SEED_EMAIL_DOMAIN}).\n"
            "Les regenerer (les donnees de test actuelles seront supprimees) ? [o/N] : "
        ).strip().lower()
    except (EOFError, OSError):
        return False
    return answer in ("o", "oui", "y", "yes")


def _delete_seed_users() -> None:
    """Supprime uniquement les comptes de test crees par ce script (et leurs
    events/rides), jamais les autres utilisateurs de la base."""
    for i in range(1, SEED_COUNT + 1):
        user = db.get_user_by_email(f"etudiant{i:02d}@{SEED_EMAIL_DOMAIN}")
        if not user:
            continue
        db.delete_rides_by_user(user.id)
        db.delete_events_by_user(user.id)
        db.delete_user(user.id)


def _create_seed_users() -> int:
    # Import tardif pour éviter tout cycle d'import avec backend.api.routes.rides
    from backend.api.routes.rides import generate_rides_for_user

    rng = random.Random(42)
    schools_geocoded = _geocode_schools()
    streets_geocoded = _geocode_streets()
    hashed = pwd_context.hash(SEED_PASSWORD)

    # Tirage sans remise pour garantir 40 noms distincts (10x10 = 100
    # combinaisons possibles ; avec remise, ~40 tirages produisaient presque
    # a coup sur des doublons — deux profils differents affichant le meme
    # nom, ce qui rendait les cards de matching totalement trompeuses).
    all_names = [f"{first} {last}" for first in FIRST_NAMES for last in LAST_NAMES]
    rng.shuffle(all_names)
    unique_names = all_names[:SEED_COUNT]

    created = 0
    for i in range(1, SEED_COUNT + 1):
        name = unique_names[i - 1]
        role = ["driver", "passenger", "both"][i % 3]
        school_name, school_addr, school_lat, school_lon = schools_geocoded[i % len(schools_geocoded)]
        street, city, street_lat, street_lon = streets_geocoded[i % len(streets_geocoded)]

        user = User(
            name=name,
            email=f"etudiant{i:02d}@{SEED_EMAIL_DOMAIN}",
            hashed_password=hashed,
            role=role,
            start_address=f"{rng.randint(1, 120)} {street}, {city}",
            start_lat=street_lat,
            start_lon=street_lon,
            time_tolerance_min=rng.randint(10, 30),
            school_address=school_addr,
            school_lat=school_lat,
            school_lon=school_lon,
        )
        try:
            user.id = db.create_user(user)
            _create_events_and_rides(user, school_name, generate_rides_for_user)
            created += 1
        except Exception as exc:
            logger.warning(f"Echec de creation du profil de test #{i:02d} ({name}): {exc!r}")

    return created


def _write_accounts_file() -> None:
    lines = [
        "Comptes de test Stud'Ride (generes par backend/database/populate.py)",
        f"Mot de passe commun a tous les comptes : {SEED_PASSWORD}",
        "",
        f"{'email':<28} {'nom':<20} {'role':<10} {'adresse de depart':<48} {'adresse ecole':<48} ecole",
        "-" * 200,
    ]
    for i in range(1, SEED_COUNT + 1):
        email = f"etudiant{i:02d}@{SEED_EMAIL_DOMAIN}"
        user = db.get_user_by_email(email)
        if not user:
            continue
        school_name = TOULOUSE_SCHOOLS[i % len(TOULOUSE_SCHOOLS)][0]
        lines.append(
            f"{user.email:<28} {user.name:<20} {user.role:<10} {user.start_address:<48} "
            f"{user.school_address:<48} {school_name}"
        )

    ACCOUNTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _geocode_query(*queries: str) -> Optional[tuple[float, float]]:
    """Geocode en essayant chaque variante de requete dans l'ordre (ex. avec
    puis sans code postal), en respectant la limite Nominatim (1 req/s)."""
    for query in queries:
        for attempt in range(2):
            matches = geocoding_service.search_address(query, limit=1)
            time.sleep(1.1)
            if matches:
                return matches[0]["lat"], matches[0]["lon"]
            logger.warning(f"Geocodage sans resultat pour '{query}' (tentative {attempt + 1}/2).")
    return None


def _geocode_schools() -> list[tuple[str, str, float, float]]:
    results = []
    fallback_count = 0
    for name, address in TOULOUSE_SCHOOLS:
        coords = _geocode_query(address)
        if coords:
            results.append((name, address, coords[0], coords[1]))
        else:
            lat, lon = config.get_campus_coords()
            logger.warning(f"Repli sur les coordonnees par defaut pour l'ecole '{name}' ({address}).")
            results.append((name, address, lat, lon))
            fallback_count += 1
    logger.info(f"Geocodage ecoles: {len(TOULOUSE_SCHOOLS) - fallback_count}/{len(TOULOUSE_SCHOOLS)} reussi(s).")
    return results


def _geocode_streets() -> list[tuple[str, str, float, float]]:
    """Géocode chaque rue (sans numéro) une seule fois — coordonnées réelles
    partagées par les utilisateurs assignés à la même rue."""
    results = []
    fallback_count = 0
    for street, city in HOME_STREETS:
        # `city` est de la forme "31770 Colomiers" — repli sans code postal
        # si la requete complete echoue (certaines rues sont mal indexees
        # avec leur code postal exact dans Nominatim/OSM).
        city_name = city.split(" ", 1)[1] if city[:5].isdigit() else city
        coords = _geocode_query(f"{street}, {city}", f"{street}, {city_name}")
        if coords:
            results.append((street, city, coords[0], coords[1]))
        else:
            lat, lon = config.get_campus_coords()
            logger.warning(f"Repli sur les coordonnees par defaut pour la rue '{street}, {city}'.")
            results.append((street, city, lat, lon))
            fallback_count += 1
    logger.info(f"Geocodage rues: {len(HOME_STREETS) - fallback_count}/{len(HOME_STREETS)} reussi(s).")
    return results


def _create_events_and_rides(user: User, school_name: str, generate_rides_for_user) -> None:
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    for day_offset in (0, 2):  # lundi, mercredi
        day = next_monday + timedelta(days=day_offset)
        event = Event(
            user_id=user.id,
            title=f"Cours a {school_name}",
            start_time=day.replace(hour=8, minute=0, second=0, microsecond=0),
            end_time=day.replace(hour=12, minute=0, second=0, microsecond=0),
            location=school_name,
        )
        event.id = db.create_event(event)
    generate_rides_for_user(user)
