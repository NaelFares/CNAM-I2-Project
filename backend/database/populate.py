"""
Peuplement BD – jeu de donnees de demonstration, en developpement uniquement.
Appele systematiquement par setup.run_startup() a chaque demarrage.

Le jeu est pense pour etre teste sur UNE semaine : la semaine de cours qui
suit le demarrage (lundi a vendredi), recalculee a chaque regeneration pour
rester dans le futur. Tous les emplois du temps, trajets et reservations de
demonstration y sont regroupes. Deux exceptions, inevitables :
- l'historique (courses terminees et avis) est forcement dans le passe ;
- une course "en cours" est placee le jour meme, pour tester le suivi.

Les coordonnees sont ecrites en dur (geocodees une fois pour toutes) : aucun
appel reseau au demarrage, et une generation identique a chaque fois.
Toutes les operations sont idempotentes.
"""
import logging
import os
import random
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import NamedTuple, Optional
from zoneinfo import ZoneInfo

from passlib.context import CryptContext
from psycopg2.extras import RealDictCursor

from backend.core.config import config
from backend.database.manager import db
from backend.models.event import Event
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import MatchingService, time_tolerance_min
from backend.services.route_estimate import AVERAGE_SPEED_KMH, ROAD_FACTOR, estimate_route

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fuseau des heures de trajets (stockees sans fuseau, en heure locale).
DEMO_TIMEZONE = ZoneInfo("Europe/Paris")

SEED_PASSWORD = "Test1234!"
SEED_COUNT = 40
SEED_EMAIL_DOMAIN = "studride-test.fr"
ACCOUNTS_FILE = Path(__file__).parent / "seed_accounts.txt"

# Sous-ensemble du catalogue (cf. backend/api/constants.py) suffisant pour
# varier les profils de demo sans les rendre illisibles.
SEED_MUSIC_GENRES = ["pop", "rap", "rnb", "shatta", "latino", "reggae", "afrobeat", "rock", "electro", "jazz"]


class School(NamedTuple):
    name: str
    address: str
    lat: float
    lon: float
    # Emploi du temps de la semaine : jour (0 = lundi) -> (debut, fin).
    timetable: dict


# Chaque ecole a son propre emploi du temps : les horaires varient selon le
# jour et l'ecole, mais les etudiants d'une meme ecole partent ensemble, ce
# qui donne des correspondances. Le CNAM a des cours du soir.
SCHOOLS = {
    "insa": School("INSA Toulouse", "135 Avenue de Rangueil, 31077 Toulouse", 43.572236, 1.468883, {
        0: ("08:00", "12:00"), 1: ("08:00", "17:00"), 2: ("10:00", "12:00"), 3: ("08:00", "16:00"), 4: ("09:00", "12:00"),
    }),
    "n7": School("ENSEEIHT (N7)", "2 Rue Charles Camichel, 31071 Toulouse", 43.602128, 1.45531, {
        0: ("08:00", "17:00"), 1: ("10:00", "18:00"), 2: ("08:00", "12:00"), 3: ("08:00", "17:00"), 4: ("08:00", "12:00"),
    }),
    "iut": School("IUT Blagnac", "1 Place Georges Brassens, 31703 Blagnac", 43.649508, 1.37487, {
        0: ("09:00", "17:00"), 1: ("08:00", "16:00"), 2: ("08:00", "12:00"), 3: ("09:00", "17:00"), 4: ("08:00", "12:00"),
    }),
    "capitole": School("Université Toulouse Capitole", "2 Rue du Doyen Gabriel Marty, 31042 Toulouse", 43.606136, 1.438197, {
        0: ("10:00", "18:00"), 1: ("08:00", "12:00"), 2: ("10:00", "16:00"), 3: ("10:00", "18:00"), 4: ("09:00", "12:00"),
    }),
    "jj": School("Université Toulouse Jean Jaurès", "5 Allée Antonio Machado, 31100 Toulouse", 43.578375, 1.401, {
        0: ("08:00", "12:00"), 1: ("10:00", "16:00"), 2: ("08:00", "12:00"), 3: ("10:00", "18:00"), 4: ("10:00", "12:00"),
    }),
    "cnam": School("CNAM Occitanie Toulouse", "118 Route de Narbonne, 31062 Toulouse", 43.556395, 1.467099, {
        0: ("18:00", "21:00"), 1: ("18:00", "21:00"), 3: ("18:00", "21:00"),
    }),
}


class SeedProfile(NamedTuple):
    first_name: str
    last_name: str
    gender: str
    street: str
    city: str
    lat: float
    lon: float
    school: str
    # Places proposees aux passagers ; None = pas de voiture.
    car_seats: Optional[int]


# Un profil par compte, dans l'ordre etudiant01..40. Le genre correspond au
# prenom ("autre" pour des prenoms mixtes). Les domiciles sont de vraies rues
# reparties sur la metropole. La plupart des etudiants habitent du cote de leur
# ecole, mais pas tous : le matching sait deposer un passager en chemin, meme
# s'il ne va pas a la meme ecole que le conducteur.
#
# Comptes a retenir pour les tests :
# - etudiant01 (Lea, INSA, passagere) : aucune reservation dans la semaine de
#   demo, pour tester la recherche librement ; une course en cours aujourd'hui
#   et des courses passees a noter (sa derniere avec chaque conducteur).
# - etudiant02 (Thomas, INSA, conducteur) : palier "Experimente".
# - etudiant04 et etudiant06 : palier "Intermediaire".
# - etudiant30 (Julie, N7, conductrice) : recoit des demandes a accepter.
# Cas de depose en chemin (ecoles differentes) :
# - etudiant10 (Camille, Castanet -> N7) passe devant l'INSA : elle peut y
#   deposer Lea (etudiant01) le lundi a 8h (+8 min environ), et la ramener
#   chez elle le mercredi a 12h, sur sa route du retour ;
# - etudiant13 et etudiant19 (Jade et Louise) habitent Blagnac et vont a
#   l'INSA, mais trop loin l'une de l'autre (detour > 12 min) : Jade n'a
#   aucune correspondance, cas utile pour tester l'ecran sans resultat.
SEED_PROFILES = [
    SeedProfile("Léa", "Martin", "femme", "Avenue Tolosane", "31520 Ramonville-Saint-Agne", 43.549654, 1.470963, "insa", None),
    SeedProfile("Thomas", "Bernard", "homme", "Avenue de Rangueil", "31400 Toulouse", 43.569934, 1.467815, "insa", 3),
    SeedProfile("Manon", "Dubois", "femme", "Avenue Saint-Exupéry", "31400 Toulouse", 43.587389, 1.461375, "insa", 3),
    SeedProfile("Hugo", "Petit", "homme", "Rue Bayard", "31000 Toulouse", 43.608995, 1.448031, "n7", 4),
    SeedProfile("Chloé", "Durand", "femme", "Allées Jean Jaurès", "31000 Toulouse", 43.607907, 1.452144, "n7", None),
    SeedProfile("Inès", "Leroy", "femme", "Avenue du Général de Gaulle", "31700 Blagnac", 43.640033, 1.378962, "iut", 2),
    SeedProfile("Nathan", "Moreau", "homme", "Rue de l'Oratoire", "31770 Colomiers", 43.609921, 1.344498, "iut", 3),
    SeedProfile("Sarah", "Simon", "femme", "Avenue des Minimes", "31200 Toulouse", 43.619046, 1.436295, "capitole", None),
    SeedProfile("Enzo", "Laurent", "homme", "Rue Gaston Doumergue", "31170 Tournefeuille", 43.582911, 1.339997, "jj", 3),
    SeedProfile("Camille", "Roux", "autre", "Avenue de Toulouse", "31320 Castanet-Tolosan", 43.522236, 1.49496, "n7", 2),
    SeedProfile("Emma", "Garcia", "femme", "Avenue de Toulouse", "31520 Ramonville-Saint-Agne", 43.54792, 1.471917, "insa", 2),
    SeedProfile("Louis", "Fournier", "homme", "Rue de la Colombette", "31000 Toulouse", 43.604463, 1.452602, "n7", 3),
    SeedProfile("Jade", "Girard", "femme", "Rue de la République", "31700 Blagnac", 43.662049, 1.36392, "insa", None),
    SeedProfile("Mathis", "Bonnet", "homme", "Boulevard de Suisse", "31200 Toulouse", 43.619063, 1.423355, "capitole", 4),
    SeedProfile("Lina", "Mercier", "femme", "Avenue du Marquisat", "31170 Tournefeuille", 43.569748, 1.334494, "jj", 2),
    SeedProfile("Adam", "Fabre", "homme", "Avenue de Gameville", "31650 Saint-Orens-de-Gameville", 43.549252, 1.536048, "cnam", None),
    SeedProfile("Zoé", "Lambert", "femme", "Avenue de la Gare", "31320 Castanet-Tolosan", 43.513936, 1.528037, "insa", None),
    SeedProfile("Rayan", "Rousseau", "homme", "Avenue de Lyon", "31500 Toulouse", 43.614565, 1.451469, "n7", None),
    SeedProfile("Louise", "Vincent", "femme", "Rue du Vieux-Blagnac", "31700 Blagnac", 43.633611, 1.39939, "insa", 3),
    SeedProfile("Théo", "Muller", "homme", "Rue des Fontaines", "31300 Toulouse", 43.60088, 1.419311, "capitole", None),
    SeedProfile("Alice", "Faure", "femme", "Avenue de Toulouse", "31270 Cugnaux", 43.540182, 1.346566, "jj", None),
    SeedProfile("Karim", "André", "homme", "Rue de l'Autan", "31670 Labège", 43.530641, 1.534279, "cnam", 3),
    SeedProfile("Nora", "Blanc", "femme", "Avenue de Toulouse", "31650 Saint-Orens-de-Gameville", 43.564399, 1.51493, "insa", None),
    SeedProfile("Paul", "Guerin", "homme", "Avenue de Toulouse", "31130 Balma", 43.609636, 1.494064, "n7", 2),
    SeedProfile("Yasmine", "Boyer", "femme", "Allée de l'Adour", "31770 Colomiers", 43.605514, 1.32098, "iut", None),
    SeedProfile("Jules", "Garnier", "homme", "Avenue de Grande-Bretagne", "31300 Toulouse", 43.603869, 1.406525, "capitole", 3),
    SeedProfile("Clara", "Chevalier", "femme", "Avenue de Francazal", "31270 Cugnaux", 43.528801, 1.350493, "jj", 4),
    SeedProfile("Alex", "François", "autre", "Route de Lavaur", "31130 Balma", 43.634385, 1.492463, "cnam", None),
    SeedProfile("Nolan", "Legrand", "homme", "Avenue Jean Rieux", "31500 Toulouse", 43.580066, 1.482599, "insa", None),
    SeedProfile("Julie", "Gauthier", "femme", "Avenue de Toulouse", "31240 L'Union", 43.649478, 1.471787, "n7", 3),
    SeedProfile("Sami", "Perrin", "homme", "Route de Fronton", "31140 Aucamville", 43.669483, 1.428399, "capitole", None),
    SeedProfile("Lucie", "Robin", "femme", "Route d'Albi", "31200 Toulouse", 43.644187, 1.468475, "capitole", 2),
    SeedProfile("Maxime", "Clément", "homme", "Avenue Jacques Douzans", "31600 Muret", 43.471854, 1.330744, "jj", None),
    SeedProfile("Maëlys", "Morin", "femme", "Rue de Metz", "31000 Toulouse", 43.599949, 1.44187, "cnam", None),
    SeedProfile("Charlie", "Nicolas", "autre", "Avenue des Pyrénées", "31240 L'Union", 43.657843, 1.483338, "n7", None),
    SeedProfile("Bastien", "Henry", "homme", "Avenue de Fronton", "31200 Toulouse", 43.648482, 1.432898, "n7", 2),
    SeedProfile("Anaïs", "Roussel", "femme", "Route de Toulouse", "31770 Colomiers", 43.614664, 1.298805, "capitole", None),
    SeedProfile("Yanis", "Mathieu", "homme", "Avenue des Pyrénées", "31830 Plaisance-du-Touch", 43.563957, 1.292682, "jj", 3),
    SeedProfile("Sacha", "Gautier", "autre", "Boulevard Vincent Auriol", "31170 Tournefeuille", 43.587498, 1.349873, "capitole", None),
    SeedProfile("Lucas", "Masson", "homme", "Avenue de Lombez", "31300 Toulouse", 43.593859, 1.409374, "jj", None),
]

# Un compte sur cinq (03, 08, 13...) a cours un quart d'heure apres les autres
# (autre groupe de TD) : la tolerance horaire entre alors en jeu dans le
# matching.
LATE_GROUP_OFFSET = timedelta(minutes=15)

# Detour maximal (a vol d'oiseau) pour les reservations de demo : environ
# 3 km de route en plus, soit une dizaine de minutes, sous MAX_DETOUR_MIN.
SEED_MAX_DETOUR_KM = 3.0

# Compte passager principal des tests : historique, course en cours, avis.
FREE_TEST_ACCOUNT = 1
# Comptes passagers laisses libres dans la semaine de demo (aucune
# reservation), pour tester la recherche et la reservation a la main depuis
# plusieurs ecoles et quartiers : Lea (INSA, Ramonville), Chloe (N7, centre),
# Theo (Capitole, Saint-Cyprien), Alice (Jean Jaures, Cugnaux).
FREE_TEST_ACCOUNTS = (1, 5, 20, 21)

# Courses terminees a generer par conducteur (numero de compte -> nombre),
# pour que les paliers d'experience soient visibles. Les autres conducteurs
# en ont quelques-unes.
HISTORY_RIDES_BY_DRIVER = {2: 52, 4: 22, 6: 21}
DEFAULT_HISTORY_RIDES = 3

RATING_COMMENTS = {
    5: ["Très ponctuel, trajet agréable.", "Parfait, je recommande.", "Super ambiance, merci !", ""],
    4: ["Bon trajet, un peu de retard au départ.", "Sympa, conduite prudente.", ""],
    3: ["Correct, mais attente au point de rendez-vous.", "Trajet un peu long."],
}


def run_populate() -> None:
    if not config.is_development():
        return

    if db.get_user_by_email(_seed_email(1)):
        if _should_reset_seed():
            logger.info("Reinitialisation du seed de test demandee.")
            _delete_seed_users()
            _create_seed_dataset()
        else:
            logger.info("Seed de test conserve tel quel.")
            created = _ensure_existing_seed_rides()
            logger.info("%s trajets de test manquants crees.", created)
    else:
        _create_seed_dataset()

    selected = _ensure_seed_selections()
    logger.info("%s inscriptions de test creees.", selected)
    _write_accounts_file()


def _seed_email(index: int) -> str:
    return f"etudiant{index:02d}@{SEED_EMAIL_DOMAIN}"


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
    events/rides), jamais les autres utilisateurs de la base. Reservations et
    avis lies partent en cascade."""
    for i in range(1, SEED_COUNT + 1):
        user = db.get_user_by_email(_seed_email(i))
        if not user:
            continue
        db.delete_rides_by_user(user.id)
        db.delete_events_by_user(user.id)
        db.delete_user(user.id)


# --- Creation du jeu complet ---

def _create_seed_dataset(now: Optional[datetime] = None) -> None:
    now = now or _local_now()
    users = _create_seed_users()
    logger.info("%s/%s profils de test crees.", len(users), SEED_COUNT)
    if len(users) < SEED_COUNT:
        return
    for index, user in users.items():
        _ensure_seed_rides(user, index, now)
    completed = _create_history(users, now)
    logger.info("%s courses terminees creees pour l'historique.", completed)
    _create_ride_in_progress(users, now)


def _create_seed_users() -> dict[int, User]:
    """Cree les 40 comptes ; retourne {numero de compte: User}."""
    rng = random.Random(42)
    hashed = pwd_context.hash(SEED_PASSWORD)
    users = {}
    for index, profile in enumerate(SEED_PROFILES, start=1):
        school = SCHOOLS[profile.school]
        # Preferences reparties pour que les cards de matching affichent des
        # combinaisons variees ; aucun compte de test n'a de photo.
        music_preference = ["peu_importe", "avec", "sans"][index % 3]
        # Styles pioches sans remise, seulement pour ceux qui acceptent la
        # musique — cf. User.wants_music.
        music_genres = (
            rng.sample(SEED_MUSIC_GENRES, rng.randint(1, 3))
            if music_preference in ("avec", "peu_importe")
            else []
        )
        user = User(
            name=f"{profile.first_name} {profile.last_name}",
            email=_seed_email(index),
            hashed_password=hashed,
            car_seats=profile.car_seats,
            gender=profile.gender,
            music_preference=music_preference,
            music_genres=music_genres,
            smoking_preference=["peu_importe", "non_fumeur", "non_fumeur", "fumeur"][index % 4],
            start_address=f"{rng.randint(1, 120)} {profile.street}, {profile.city}",
            start_lat=profile.lat,
            start_lon=profile.lon,
            time_tolerance_min=rng.choice([10, 15, 20, 30]),
            school_address=school.address,
            school_lat=school.lat,
            school_lon=school.lon,
        )
        try:
            user.id = db.create_user(user)
            users[index] = user
        except Exception as exc:
            logger.warning("Echec de creation du profil de test #%02d (%s): %r", index, user.name, exc)
    return users


def _write_accounts_file() -> None:
    lines = [
        "Comptes de test Stud'Ride (generes par backend/database/populate.py)",
        f"Mot de passe commun a tous les comptes : {SEED_PASSWORD}",
        "",
        f"{'email':<28} {'nom':<20} {'places':<8} {'sexe':<8} "
        f"{'adresse de depart':<56} ecole",
        "-" * 150,
    ]
    for index, profile in enumerate(SEED_PROFILES, start=1):
        user = db.get_user_by_email(_seed_email(index))
        if not user:
            continue
        car_seats = str(user.car_seats) if user.car_seats is not None else "-"
        lines.append(
            f"{user.email:<28} {user.name:<20} {car_seats:<8} {user.gender:<8} "
            f"{user.start_address:<56} {SCHOOLS[profile.school].name}"
        )
    ACCOUNTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- Semaine de demonstration ---

def demo_week_monday(now: datetime) -> datetime:
    """Lundi de la semaine de demo : toujours le lundi qui suit, pour que
    toute la semaine soit dans le futur au moment des tests."""
    days_ahead = (7 - now.weekday()) % 7 or 7
    return datetime.combine((now + timedelta(days=days_ahead)).date(), time.min)


def _at(day: datetime, hhmm: str) -> datetime:
    hours, minutes = (int(part) for part in hhmm.split(":"))
    return day.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def _ensure_existing_seed_rides(now: Optional[datetime] = None) -> int:
    """Complete les trajets des comptes de test sans effacer leurs réservations."""
    created = 0
    for index in range(1, SEED_COUNT + 1):
        user = db.get_user_by_email(_seed_email(index))
        if user:
            created += _ensure_seed_rides(user, index, now)
    return created


def _ensure_seed_rides(user: User, index: int, now: Optional[datetime] = None) -> int:
    """Cree les cours de la semaine de demo et leurs allers-retours, sans doublons."""
    profile = SEED_PROFILES[index - 1]
    school = SCHOOLS[profile.school]
    offset = LATE_GROUP_OFFSET if index % 5 == 3 else timedelta(0)
    monday = demo_week_monday(now or _local_now())

    events = db.get_events_by_user(user.id)
    existing_rides = {(ride.event_id, ride.ride_type) for ride in db.get_rides_by_user(user.id)}
    home = (user.start_lat, user.start_lon, user.start_address)
    campus = (school.lat, school.lon, school.name)
    created = 0
    for weekday, (start, end) in sorted(school.timetable.items()):
        day = monday + timedelta(days=weekday)
        start_time = _at(day, start) + offset
        end_time = _at(day, end) + offset
        event = next((item for item in events if item.start_time == start_time), None)
        if event is None:
            event = Event(
                user_id=user.id,
                title=f"Cours à {school.name}",
                start_time=start_time,
                end_time=end_time,
                location=school.name,
            )
            event.id = db.create_event(event)
            events.append(event)

        for ride_type, ride_time, origin, destination in (
            ("to_campus", start_time, home, campus),
            ("from_campus", end_time, campus, home),
        ):
            if (event.id, ride_type) in existing_rides:
                continue
            db.create_ride(Ride(
                user_id=user.id,
                event_id=event.id,
                ride_type=ride_type,
                ride_time=ride_time,
                start_lat=origin[0],
                start_lon=origin[1],
                end_lat=destination[0],
                end_lon=destination[1],
                start_address=origin[2],
                end_address=destination[2],
                # Les comptes avec voiture proposent leurs trajets.
                is_offer=user.can_drive(),
            ))
            existing_rides.add((event.id, ride_type))
            created += 1
    return created


def _ensure_seed_selections() -> int:
    """Reserve des places dans la semaine de demo aupres des conducteurs dont
    la route passe par le passager. Du lundi au mercredi, la premiere demande
    d'un trajet est acceptee ; ensuite, et le jeudi et le vendredi, les
    demandes restent en attente pour que le conducteur ait des choix a faire.

    Les comptes FREE_TEST_ACCOUNTS ne sont jamais inscrits : ils servent a
    tester la recherche et la reservation a la main. Chaque demande garde sa
    prise en charge, sa depose, son heure de passage et son detour estimes,
    comme une vraie reservation, pour que le conducteur les voie."""
    accounts = {}
    for index in range(1, SEED_COUNT + 1):
        user = db.get_user_by_email(_seed_email(index))
        if user:
            accounts[index] = user
    rides_by_user = {user.id: db.get_rides_by_user(user.id) for user in accounts.values()}
    counts = db.get_ride_request_counts()
    accepted_counts = db.get_ride_selection_counts()
    now = _local_now()
    created = 0

    drivers = [user for user in accounts.values() if user.can_drive()]
    for index, passenger in accounts.items():
        if passenger.can_drive() or index in FREE_TEST_ACCOUNTS:
            continue
        reserved_times = db.get_passenger_reserved_times(passenger.id)

        for passenger_ride in rides_by_user[passenger.id]:
            if passenger_ride.status != "active" or passenger_ride.ride_time <= now:
                continue
            if passenger_ride.ride_time in reserved_times:
                continue
            # Meme critere que le matching : le conducteur doit pouvoir prendre
            # puis deposer le passager sans grand detour, quelle que soit
            # l'ecole de chacun (estimation a vol d'oiseau, sans appel reseau).
            candidates = [
                (detour_km, gap, ride.id, driver, ride)
                for driver in drivers
                for ride in rides_by_user[driver.id]
                if ride.status == "active"
                and ride.is_offer
                and ride.ride_type == passenger_ride.ride_type
                # Meme regle horaire que le matching : depose avant l'heure
                # d'arrivee, ou prise en charge apres l'heure de depart.
                for gap in [MatchingService._estimated_gap_min(ride, passenger_ride)]
                if 0 <= gap <= time_tolerance_min(passenger)
                for detour_km in [MatchingService._straight_line_detour_km(ride, passenger_ride)]
                if detour_km <= SEED_MAX_DETOUR_KM
            ]
            for *_, driver, ride in sorted(candidates, key=lambda item: item[:3]):
                # Garder une place libre, sauf dans les voitures à une seule place passager.
                seed_limit = max(1, min(2, driver.car_seats - 1))
                if counts.get(ride.id, 0) >= seed_limit:
                    continue
                result = db.select_ride(ride.id, passenger.id, _seed_stop(ride, passenger_ride))
                if result["status"] in ("already_selected", "time_conflict"):
                    reserved_times.add(ride.ride_time)
                    break
                if result["status"] != "selected":
                    continue
                counts[ride.id] = counts.get(ride.id, 0) + 1
                reserved_times.add(ride.ride_time)
                created += 1
                # Du lundi au mercredi, la premiere demande est acceptee ; le
                # jeudi et le vendredi, tout reste en attente, pour que chaque
                # conducteur ait des demandes a accepter ou refuser.
                if accepted_counts.get(ride.id, 0) == 0 and ride.ride_time.weekday() < 3:
                    decision = db.decide_ride_selection(ride.id, passenger.id, driver.id, "accept")
                    if decision["status"] == "accepted":
                        accepted_counts[ride.id] = 1
                break
    return created


def _seed_stop(driver_ride: Ride, passenger_ride: Ride) -> dict:
    """Prise en charge, depose, heure de passage et detour d'une reservation
    de demo, estimes sans appel reseau (OSRM peut encore etre en train de
    preparer sa carte au premier demarrage)."""
    pickup, dropoff = MatchingService._pickup_and_dropoff(driver_ride, passenger_ride)
    leg = MatchingService._leg_to_passenger(driver_ride, passenger_ride)
    passage = MatchingService._passage_time(driver_ride, estimate_route(list(leg))["duration_s"] if leg else 0.0)
    detour_km = MatchingService._straight_line_detour_km(driver_ride, passenger_ride)
    return {
        "pickup": (passenger_ride.start_lat, passenger_ride.start_lon) if pickup else None,
        "dropoff": (passenger_ride.end_lat, passenger_ride.end_lon) if dropoff else None,
        "passage_time": passage.strftime("%H:%M"),
        # Detour a vol d'oiseau converti en minutes, avec la meme hypothese
        # que l'estimation de secours (route 30 % plus longue, 30 km/h).
        "detour_min": round(max(0.0, detour_km) * ROAD_FACTOR / AVERAGE_SPEED_KMH * 60, 1),
    }


# --- Historique et course en cours ---

def _past_weekdays(now: datetime):
    """Jours ouvres passes, du plus recent au plus ancien (hier d'abord)."""
    day = datetime.combine(now.date(), time.min)
    while True:
        day -= timedelta(days=1)
        if day.weekday() < 5:
            yield day


def _create_history(users: dict[int, User], now: datetime) -> int:
    """Cree des courses terminees dans le passe, avec des avis.

    Les courses sont deja archivees et leurs quatre etapes confirmees : elles
    alimentent les paliers d'experience et la liste des avis recus. Chaque
    conducteur fait l'aller du matin et le retour du soir avec un passager
    de son ecole, jamais deux voitures a la fois pour un meme passager. La
    course la plus recente du compte FREE_TEST_ACCOUNT avec chaque conducteur
    reste sans avis, pour tester la notation ; ses autres courses sont notees.
    """
    planned = _plan_history(users, now)
    # Derniere course du compte de test avec chaque conducteur : a noter.
    to_rate = {}
    for ride_time, driver_index, passenger_index in planned:
        if passenger_index == FREE_TEST_ACCOUNT:
            to_rate[driver_index] = max(ride_time, to_rate.get(driver_index, ride_time))

    rng = random.Random(7)
    # Creation dans l'ordre chronologique : les listes de l'interface sont
    # triees par ordre de creation, l'historique doit donc l'etre aussi.
    for ride_time, driver_index, passenger_index in sorted(planned):
        driver, passenger = users[driver_index], users[passenger_index]
        school = SCHOOLS[SEED_PROFILES[driver_index - 1].school]
        to_campus = ride_time.hour < 12
        ride_id = db.create_ride(Ride(
            user_id=driver.id,
            ride_type="to_campus" if to_campus else "from_campus",
            ride_time=ride_time,
            start_lat=driver.start_lat if to_campus else school.lat,
            start_lon=driver.start_lon if to_campus else school.lon,
            end_lat=school.lat if to_campus else driver.start_lat,
            end_lon=school.lon if to_campus else driver.start_lon,
            start_address=driver.start_address if to_campus else school.name,
            end_address=school.name if to_campus else driver.start_address,
            status="archived",
            archived_at=_aware(ride_time + timedelta(hours=3)),
            is_offer=True,
        ))
        selection_id = _insert_completed_selection(ride_id, passenger.id, ride_time)

        if passenger_index == FREE_TEST_ACCOUNT:
            if to_rate[driver_index] != ride_time:
                _insert_rating(selection_id, passenger.id, driver.id, rng, ride_time)
            continue
        if rng.random() < 0.8:
            _insert_rating(selection_id, passenger.id, driver.id, rng, ride_time)
        if rng.random() < 0.5:
            _insert_rating(selection_id, driver.id, passenger.id, rng, ride_time)
    return len(planned)


def _plan_history(users: dict[int, User], now: datetime) -> list[tuple[datetime, int, int]]:
    """Choisit les courses passees : (heure, conducteur, passager).

    Chaque conducteur remonte le temps, matin et soir, et emmene a tour de
    role un passager de son ecole qui n'est pas deja dans une autre voiture
    a cette heure-la.
    """
    passengers_by_school = {}
    for index, user in users.items():
        if not user.can_drive():
            passengers_by_school.setdefault(SEED_PROFILES[index - 1].school, []).append(index)
    busy = set()
    planned = []
    for driver_index, driver in users.items():
        if not driver.can_drive():
            continue
        passengers = passengers_by_school.get(SEED_PROFILES[driver_index - 1].school, [])
        ride_count = HISTORY_RIDES_BY_DRIVER.get(driver_index, DEFAULT_HISTORY_RIDES)
        slots = (_at(day, hhmm) for day in _past_weekdays(now) for hhmm in ("08:00", "17:00"))
        done = turn = 0
        # Borne de securite : une ecole sans passager libre ne doit pas
        # faire tourner la boucle indefiniment.
        for ride_time in (next(slots) for _ in range(ride_count * 4)):
            if done == ride_count or not passengers:
                break
            free = [p for p in passengers if (p, ride_time) not in busy]
            if not free:
                continue
            passenger_index = free[turn % len(free)]
            turn += 1
            busy.add((passenger_index, ride_time))
            planned.append((ride_time, driver_index, passenger_index))
            done += 1
    return planned


def _create_ride_in_progress(users: dict[int, User], now: datetime) -> None:
    """Course du jour deja commencee : le conducteur a pris en charge le
    compte de test et celui-ci a confirme etre a bord. Sert a tester la fin
    du suivi, et le refus d'annuler une course commencee."""
    driver = users[2]
    passenger = users[FREE_TEST_ACCOUNT]
    school = SCHOOLS[SEED_PROFILES[1].school]
    ride_time = now.replace(second=0, microsecond=0) - timedelta(minutes=15)
    ride_id = db.create_ride(Ride(
        user_id=driver.id,
        ride_type="to_campus",
        ride_time=ride_time,
        start_lat=driver.start_lat,
        start_lon=driver.start_lon,
        end_lat=school.lat,
        end_lon=school.lon,
        start_address=driver.start_address,
        end_address=school.name,
        is_offer=True,
    ))
    _execute(
        """
        INSERT INTO ride_selections
            (ride_id, passenger_id, status, selected_at, driver_picked_up_at, passenger_onboard_at)
        VALUES (%s, %s, 'accepted', %s, %s, %s)
        """,
        (ride_id, passenger.id, ride_time - timedelta(days=1),
         ride_time + timedelta(minutes=5), ride_time + timedelta(minutes=6)),
    )


def _insert_completed_selection(ride_id: int, passenger_id: int, ride_time: datetime) -> int:
    """Reservation acceptee dont les quatre etapes du suivi sont confirmees."""
    return _execute(
        """
        INSERT INTO ride_selections
            (ride_id, passenger_id, status, selected_at,
             driver_picked_up_at, passenger_onboard_at, driver_completed_at, passenger_arrived_at)
        VALUES (%s, %s, 'accepted', %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (ride_id, passenger_id, ride_time - timedelta(days=2),
         ride_time + timedelta(minutes=2), ride_time + timedelta(minutes=3),
         ride_time + timedelta(minutes=25), ride_time + timedelta(minutes=26)),
    )["id"]


def _insert_rating(selection_id: int, rater_id: int, rated_id: int, rng: random.Random, ride_time: datetime) -> None:
    score = rng.choice([5, 5, 5, 4, 4, 3])
    _execute(
        """
        INSERT INTO ride_ratings (ride_selection_id, rater_id, rated_id, score, comment, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ride_selection_id, rater_id) DO NOTHING
        """,
        (selection_id, rater_id, rated_id, score, rng.choice(RATING_COMMENTS[score]),
         ride_time + timedelta(hours=1)),
    )


def _local_now() -> datetime:
    """Heure de Toulouse, sans fuseau, comme les heures de trajets en base.
    Le conteneur tourne en UTC : datetime.now() y serait decale."""
    return datetime.now(DEMO_TIMEZONE).replace(tzinfo=None)


def _aware(moment: datetime) -> datetime:
    """Heure de Toulouse munie de son fuseau. Sans fuseau, PostgreSQL lirait
    l'heure comme de l'UTC dans les colonnes TIMESTAMPTZ (horodatages du
    suivi, des avis, de l'archivage), et l'interface les decalerait."""
    return moment.replace(tzinfo=DEMO_TIMEZONE) if moment.tzinfo is None else moment


def _execute(query: str, params: tuple) -> Optional[dict]:
    """Execute une ecriture et retourne la ligne RETURNING, le cas echeant."""
    params = tuple(_aware(value) if isinstance(value, datetime) else value for value in params)
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params)
    row = cursor.fetchone() if cursor.description else None
    conn.commit()
    conn.close()
    return row
