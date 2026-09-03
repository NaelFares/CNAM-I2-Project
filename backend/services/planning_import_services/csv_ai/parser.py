"""
Parseur d'import CSV assisté par IA.

Flux :
  1. Lecture du CSV (détection automatique encodage + séparateur)
  2. Construction d'un échantillon minimal (en-têtes + 1 ligne), ou des en-têtes
     seuls lorsque le Privacy mode est activé
  3. Appel au fournisseur IA (Ollama ou Groq) pour obtenir le mapping de colonnes
  4. Reconstruction des événements sur tout le fichier
  5. Score de confiance final
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.core.config import config
from backend.models.event import Event
from .providers import get_provider

logger = logging.getLogger(__name__)


@dataclass
class CSVParseResult:
    events: list[Event]
    confidence_score: float
    requires_user_review: bool
    mapping_explanation: str


class CsvAiPlanningParser:
    """Parse un fichier CSV de planning via un mapping de colonnes assisté par IA."""

    _RESOURCES_DIR = Path(__file__).resolve().parent
    _PROMPTS_DIR = _RESOURCES_DIR / "prompts"
    _SCHEMAS_DIR = _RESOURCES_DIR / "schemas"

    @staticmethod
    def parse(file_content: bytes, privacy_mode: bool = False) -> CSVParseResult:
        if not config.AI_IMPORT_ENABLED:
            raise ValueError("Le workflow IA d'import CSV est desactive.")

        try:
            df, encoding = CsvAiPlanningParser._read_csv(file_content)
            available_columns = [str(col) for col in df.columns.tolist()]
            sample_payload = CsvAiPlanningParser._build_sample_payload(df, privacy_mode=privacy_mode)
            logger.info(
                "CSV IA import: lines=%s columns=%s encoding=%s privacy_mode=%s",
                len(df.index), available_columns, encoding, privacy_mode,
            )

            last_error: Exception | None = None
            for attempt in range(1, 3):
                try:
                    mapping = CsvAiPlanningParser._request_ai_mapping(
                        sample_payload=sample_payload,
                        available_columns=available_columns,
                        refinement_reason=str(last_error) if last_error else None,
                        attempt=attempt,
                    )
                except Exception as exc:
                    last_error = exc
                    logger.warning("CSV IA mapping request failed: attempt=%s error=%s", attempt, exc)
                    continue

                try:
                    events, success_ratio = CsvAiPlanningParser._build_events(df, mapping)
                    confidence = CsvAiPlanningParser._compute_confidence(mapping, success_ratio)
                    explanation = str(mapping.get("summary", "Mapping IA applique."))
                    if attempt > 1:
                        explanation = f"{explanation} (corrige a la tentative {attempt})"
                    logger.info(
                        "CSV IA import success: attempt=%s events=%s confidence=%.2f",
                        attempt, len(events), confidence,
                    )
                    return CSVParseResult(
                        events=events,
                        confidence_score=confidence,
                        requires_user_review=confidence < config.AI_IMPORT_CONFIDENCE_THRESHOLD,
                        mapping_explanation=explanation,
                    )
                except Exception as exc:
                    last_error = exc
                    logger.warning("CSV IA attempt failed: attempt=%s error=%s", attempt, exc)

            raise ValueError(f"Echec mapping CSV IA apres 2 tentatives: {last_error}")
        except Exception as exc:
            raise ValueError(f"Erreur lors du parsing CSV IA: {exc}") from exc

    # ------------------------------------------------------------------
    # Lecture CSV
    # ------------------------------------------------------------------

    @staticmethod
    def _read_csv(file_content: bytes) -> tuple[pd.DataFrame, str]:
        for encoding in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            try:
                df = pd.read_csv(
                    pd.io.common.BytesIO(file_content),
                    encoding=encoding,
                    sep=None,
                    engine="python",
                    dtype=str,
                    keep_default_na=False,
                )
                if df.empty and not df.columns.tolist():
                    raise ValueError("CSV vide")
                return df, encoding
            except Exception:
                continue
        raise ValueError("Impossible de lire le CSV : aucun encodage compatible")

    @staticmethod
    def _build_sample_payload(df: pd.DataFrame, privacy_mode: bool = False) -> dict[str, Any]:
        rows = []
        if not privacy_mode:
            rows = [{str(k): str(v) for k, v in row.to_dict().items()} for _, row in df.head(1).iterrows()]
        return {"headers": [str(col) for col in df.columns.tolist()], "sample_rows": rows}

    # ------------------------------------------------------------------
    # Appel IA
    # ------------------------------------------------------------------

    @staticmethod
    def _request_ai_mapping(
        sample_payload: dict[str, Any],
        available_columns: list[str],
        refinement_reason: str | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        if not sample_payload.get("headers"):
            raise ValueError("CSV vide : aucun en-tete a envoyer au modele")

        system_prompt = CsvAiPlanningParser._load_text(CsvAiPlanningParser._PROMPTS_DIR / "system_prompt.txt")
        user_template = CsvAiPlanningParser._load_text(CsvAiPlanningParser._PROMPTS_DIR / "mapping_prompt_template.txt")
        schema = CsvAiPlanningParser._load_schema()

        user_prompt = CsvAiPlanningParser._build_user_prompt(
            user_template=user_template,
            sample_payload=sample_payload,
            available_columns=available_columns,
            refinement_reason=refinement_reason,
        )

        mapping = get_provider().call(system_prompt, user_prompt, schema)

        if "fields" not in mapping:
            raise ValueError("Reponse IA invalide : champ 'fields' manquant")

        logger.debug("CSV IA raw mapping (attempt=%s): %s", attempt, mapping)
        return mapping

    @staticmethod
    def _build_user_prompt(
        user_template: str,
        sample_payload: dict[str, Any],
        available_columns: list[str],
        refinement_reason: str | None = None,
    ) -> str:
        prompt = user_template.format(sample_payload=json.dumps(sample_payload, ensure_ascii=False, indent=2))
        prompt += "\nUtilise uniquement les noms exacts presents dans headers."
        if refinement_reason:
            prompt += (
                "\nCorrection demandee: la tentative precedente a echoue avec l'erreur: "
                f"{refinement_reason}\nPropose un mapping corrige."
            )
        return prompt

    # ------------------------------------------------------------------
    # Reconstruction des événements
    # ------------------------------------------------------------------

    @staticmethod
    def _build_events(df: pd.DataFrame, mapping: dict[str, Any]) -> tuple[list[Event], float]:
        available_columns = [str(col) for col in df.columns.tolist()]
        fields = mapping.get("fields", {})

        for target in ["title", "start_time", "end_time", "location", "description"]:
            if target not in fields:
                raise ValueError(f"Mapping IA incomplet : {target} manquant")

        resolved = CsvAiPlanningParser._resolve_mapping_fields(fields, available_columns)
        events: list[Event] = []
        total_rows = 0

        for _, row in df.iterrows():
            total_rows += 1
            row_dict = {str(k): str(v) for k, v in row.to_dict().items()}
            title = CsvAiPlanningParser._extract_text(row_dict, resolved["title"])
            start_time = CsvAiPlanningParser._extract_datetime(row_dict, resolved["start_time"])
            end_time = CsvAiPlanningParser._extract_datetime(row_dict, resolved["end_time"])

            if not title or start_time is None or end_time is None or end_time <= start_time:
                continue

            events.append(Event(
                title=title,
                start_time=start_time,
                end_time=end_time,
                location=CsvAiPlanningParser._extract_text(row_dict, resolved["location"]),
                description=CsvAiPlanningParser._extract_text(row_dict, resolved["description"]),
            ))

        if not events:
            logger.warning("Mapping IA sans evenements. mapping=%s columns=%s", mapping, available_columns)
            raise ValueError("Aucun evenement valide reconstruit depuis le mapping IA")

        return events, len(events) / total_rows if total_rows else 0.0

    @staticmethod
    def _extract_text(row: dict[str, str], spec: dict[str, Any]) -> str:
        mode = str(spec.get("mode", "single"))
        columns = spec.get("columns", []) or []

        if mode == "empty":
            return ""
        if mode == "single" and columns:
            return next((str(row.get(c, "")).strip() for c in columns if str(row.get(c, "")).strip()), "")
        if mode == "concat" and columns:
            sep = str(spec.get("separator", " "))
            return sep.join(v for c in columns if (v := str(row.get(c, "")).strip())).strip()
        if mode == "datetime_combine" and len(columns) >= 2:
            return f"{str(row.get(columns[0], '')).strip()} {str(row.get(columns[1], '')).strip()}".strip()
        return ""

    @staticmethod
    def _extract_datetime(row: dict[str, str], spec: dict[str, Any]) -> datetime | None:
        raw = CsvAiPlanningParser._extract_text(row, spec)
        if not raw:
            return None
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        return None if pd.isna(parsed) else parsed.to_pydatetime()

    @staticmethod
    def _compute_confidence(mapping: dict[str, Any], success_ratio: float) -> float:
        model_conf = float(mapping.get("overall_confidence", 0.0) or 0.0)
        fields = mapping.get("fields", {})
        field_scores = [float(fields.get(k, {}).get("confidence", 0.0) or 0.0)
                        for k in ["title", "start_time", "end_time", "location", "description"]]
        field_avg = sum(field_scores) / len(field_scores)
        score = (0.45 * model_conf) + (0.25 * field_avg) + (0.30 * max(0.0, min(1.0, success_ratio)))
        return round(max(0.0, min(1.0, score)), 2)

    # ------------------------------------------------------------------
    # Résolution des noms de colonnes
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_mapping_fields(fields: dict[str, Any], available_columns: list[str]) -> dict[str, dict[str, Any]]:
        resolved = {}
        for key, spec in fields.items():
            resolved_spec = dict(spec)
            columns = list(spec.get("columns", []) or [])
            mode = str(spec.get("mode", "single"))

            if mode == "single" and len(columns) > 1:
                resolved_spec["columns"] = [columns[0]]
            elif mode == "datetime_combine" and len(columns) >= 2 and columns[0] == columns[1]:
                first = CsvAiPlanningParser._resolve_column_name(columns[0], available_columns)
                second = CsvAiPlanningParser._resolve_second_duplicate(columns[1], available_columns, first)
                resolved_spec["columns"] = [first, second]
            else:
                resolved_spec["columns"] = [
                    CsvAiPlanningParser._resolve_column_name(c, available_columns) for c in columns
                ]
            resolved[key] = resolved_spec
        return resolved

    @staticmethod
    def _resolve_column_name(requested: str, available_columns: list[str]) -> str:
        if requested in available_columns:
            return requested
        requested_norm = CsvAiPlanningParser._normalize(requested)
        by_norm = {CsvAiPlanningParser._normalize(col): col for col in available_columns}
        if requested_norm in by_norm:
            return by_norm[requested_norm]
        for col in available_columns:
            col_norm = CsvAiPlanningParser._normalize(col)
            if col_norm.startswith(f"{requested_norm}.") or requested_norm.startswith(f"{col_norm}."):
                return col
        return requested

    @staticmethod
    def _resolve_second_duplicate(requested: str, available_columns: list[str], first: str) -> str:
        req_norm = CsvAiPlanningParser._normalize(requested)
        first_norm = CsvAiPlanningParser._normalize(first)
        for candidate in available_columns:
            if candidate == first:
                continue
            c_norm = CsvAiPlanningParser._normalize(candidate)
            if c_norm == req_norm or c_norm.startswith(f"{req_norm}.") or c_norm.startswith(f"{first_norm}."):
                return candidate
        return CsvAiPlanningParser._resolve_column_name(requested, available_columns)

    @staticmethod
    def _normalize(value: str) -> str:
        ascii_only = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only).strip().lower()

    # ------------------------------------------------------------------
    # Chargement des ressources
    # ------------------------------------------------------------------

    @staticmethod
    def _load_text(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Ressource prompt introuvable : {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _load_schema() -> dict[str, Any]:
        schema_path = CsvAiPlanningParser._SCHEMAS_DIR / "mapping_response.schema.json"
        if not schema_path.exists():
            return {"type": "object"}
        return json.loads(schema_path.read_text(encoding="utf-8"))


csv_ai_planning_parser = CsvAiPlanningParser()
