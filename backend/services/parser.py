"""
Service de parsing des emplois du temps.
Supporte les formats ICS (iCalendar) et CSV.
"""
from typing import List
from datetime import datetime
import pandas as pd
from icalendar import Calendar

from backend.models.event import Event


class ScheduleParser:
    """Parse les emplois du temps depuis différents formats"""

    @staticmethod
    def parse_ics(file_content: bytes) -> List[Event]:
        """
        Parse un fichier ICS et retourne une liste d'événements.

        Args:
            file_content: Contenu du fichier ICS en bytes

        Returns:
            Liste d'événements Event
        """
        events = []
        try:
            cal = Calendar.from_ical(file_content)
            for component in cal.walk():
                if component.name == "VEVENT":
                    # Extraction des données
                    title = str(component.get("summary", "Sans titre"))
                    start_time = component.get("dtstart").dt
                    end_time = component.get("dtend").dt
                    location = str(component.get("location", ""))
                    description = str(component.get("description", ""))

                    # Conversion en datetime si nécessaire
                    if not isinstance(start_time, datetime):
                        start_time = datetime.combine(start_time, datetime.min.time())
                    if not isinstance(end_time, datetime):
                        end_time = datetime.combine(end_time, datetime.min.time())

                    event = Event(
                        title=title,
                        start_time=start_time,
                        end_time=end_time,
                        location=location,
                        description=description,
                    )
                    events.append(event)
        except Exception as e:
            raise ValueError(f"Erreur lors du parsing ICS: {str(e)}")

        return events

    @staticmethod
    def parse_csv(file_content: bytes) -> List[Event]:
        """
        Parse un fichier CSV et retourne une liste d'événements.
        Supporte le format CNAM (Outlook export) et le format simple.

        Args:
            file_content: Contenu du fichier CSV en bytes

        Returns:
            Liste d'événements Event
        """
        events = []
        try:
            # Essayer différents encodages pour les fichiers CSV
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(pd.io.common.BytesIO(file_content), encoding=encoding)
                    break
                except (UnicodeDecodeError, Exception):
                    continue

            if df is None:
                raise ValueError("Impossible de lire le fichier CSV avec les encodages supportés")

            # Détection du format CNAM (Outlook)
            if "Objet" in df.columns:
                events = ScheduleParser._parse_cnam_format(df)
            # Format simple avec colonnes directes
            elif all(col in df.columns for col in ["title", "start_time", "end_time"]):
                events = ScheduleParser._parse_simple_format(df)
            else:
                raise ValueError(
                    "Format CSV non reconnu. Formats supportés: "
                    "CNAM (export Outlook) ou format simple (title, start_time, end_time)"
                )

        except Exception as e:
            raise ValueError(f"Erreur lors du parsing CSV: {str(e)}")

        return events

    @staticmethod
    def _parse_cnam_format(df: pd.DataFrame) -> List[Event]:
        """
        Parse le format CSV exporté depuis Outlook (format CNAM).

        Args:
            df: DataFrame pandas contenant les données

        Returns:
            Liste d'événements Event
        """
        events = []

        # Les colonnes du format CNAM (Outlook export)
        # Note: Il peut y avoir des colonnes dupliquées, pandas les renomme
        cols = df.columns.tolist()

        # Trouver les indices des colonnes "Début" et "Fin"
        debut_cols = [i for i, col in enumerate(cols) if col.startswith("Début")]
        fin_cols = [i for i, col in enumerate(cols) if col.startswith("Fin")]

        for _, row in df.iterrows():
            try:
                # Extraire le titre (colonne "Objet")
                title = str(row["Objet"]) if "Objet" in row else ""

                # Extraire et combiner date et heure de début
                if len(debut_cols) >= 2:
                    date_debut = str(row.iloc[debut_cols[0]])
                    heure_debut = str(row.iloc[debut_cols[1]])
                    start_time = pd.to_datetime(f"{date_debut} {heure_debut}", format="%d/%m/%Y %H:%M:%S", errors='coerce')
                else:
                    continue

                # Extraire et combiner date et heure de fin
                if len(fin_cols) >= 2:
                    date_fin = str(row.iloc[fin_cols[0]])
                    heure_fin = str(row.iloc[fin_cols[1]])
                    end_time = pd.to_datetime(f"{date_fin} {heure_fin}", format="%d/%m/%Y %H:%M:%S", errors='coerce')
                else:
                    continue

                # Vérifier que les dates sont valides
                if pd.isna(start_time) or pd.isna(end_time):
                    continue

                # Extraire l'emplacement
                location = str(row.get("Emplacement", ""))

                # Extraire la description
                description = str(row.get("Description", ""))

                event = Event(
                    title=title,
                    start_time=start_time.to_pydatetime(),
                    end_time=end_time.to_pydatetime(),
                    location=location,
                    description=description,
                )
                events.append(event)

            except Exception as e:
                # Ignorer les lignes invalides et continuer
                continue

        return events

    @staticmethod
    def _parse_simple_format(df: pd.DataFrame) -> List[Event]:
        """
        Parse le format CSV simple avec colonnes directes.

        Args:
            df: DataFrame pandas contenant les données

        Returns:
            Liste d'événements Event
        """
        events = []

        for _, row in df.iterrows():
            try:
                start_time = pd.to_datetime(row["start_time"])
                end_time = pd.to_datetime(row["end_time"])

                event = Event(
                    title=str(row["title"]),
                    start_time=start_time.to_pydatetime(),
                    end_time=end_time.to_pydatetime(),
                    location=str(row.get("location", "")),
                    description=str(row.get("description", "")),
                )
                events.append(event)
            except Exception as e:
                # Ignorer les lignes invalides
                continue

        return events


# Instance globale
parser = ScheduleParser()
