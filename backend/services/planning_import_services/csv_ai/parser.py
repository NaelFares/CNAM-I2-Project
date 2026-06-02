"""CSV planning import parser assisted by Ollama."""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests import RequestException

from backend.core.config import config
from backend.models.event import Event

logger = logging.getLogger(__name__)


@dataclass
class CSVParseResult:
    events: list[Event]
    confidence_score: float
    requires_user_review: bool
    mapping_explanation: str


class CsvAiPlanningParser:
    """Parse planning CSV files through an AI-assisted column mapping workflow."""

    _RESOURCES_DIR = Path(__file__).resolve().parent
    _PROMPTS_DIR = _RESOURCES_DIR / "prompts"
    _SCHEMAS_DIR = _RESOURCES_DIR / "schemas"

    @staticmethod
    def parse(file_content: bytes) -> CSVParseResult:
        """
        Parse a CSV file through the AI mapping workflow.

        The prompt sends only a compact sample of headers and the first row.
        """
        if not config.AI_IMPORT_ENABLED:
            raise ValueError("Le workflow IA d'import CSV est desactive.")

        try:
            df, encoding = CsvAiPlanningParser._read_csv(file_content)
            available_columns = [str(col) for col in df.columns.tolist()]
            sample_payload = CsvAiPlanningParser._build_sample_payload(df)
            logger.info("CSV IA import: lines=%s columns=%s encoding=%s", len(df.index), available_columns, encoding)

            last_error: Exception | None = None
            max_attempts = 2
            for attempt in range(1, max_attempts + 1):
                refinement_reason = str(last_error) if last_error else None
                try:
                    mapping = CsvAiPlanningParser._request_ai_mapping(
                        sample_payload=sample_payload,
                        available_columns=available_columns,
                        refinement_reason=refinement_reason,
                        attempt=attempt,
                    )
                except Exception as exc:  # pragma: no cover - runtime dependent on model output
                    last_error = exc
                    logger.warning("CSV IA mapping request failed: attempt=%s error=%s", attempt, exc)
                    continue

                try:
                    events, success_ratio = CsvAiPlanningParser._build_events(df, mapping)
                    confidence = CsvAiPlanningParser._compute_confidence(mapping, success_ratio)
                    requires_review = confidence < config.AI_IMPORT_CONFIDENCE_THRESHOLD
                    explanation = str(mapping.get("summary", "Mapping IA applique."))
                    if attempt > 1:
                        explanation = f"{explanation} (corrige a la tentative {attempt})"

                    logger.info(
                        "CSV IA import success: attempt=%s events=%s success_ratio=%.2f confidence=%.2f",
                        attempt,
                        len(events),
                        success_ratio,
                        confidence,
                    )
                    return CSVParseResult(
                        events=events,
                        confidence_score=confidence,
                        requires_user_review=requires_review,
                        mapping_explanation=explanation,
                    )
                except Exception as exc:  # pragma: no cover - runtime dependent on model output
                    last_error = exc
                    logger.warning("CSV IA attempt failed: attempt=%s error=%s", attempt, exc)

            raise ValueError(f"Echec mapping CSV IA apres {max_attempts} tentatives: {last_error}")
        except Exception as exc:
            raise ValueError(f"Erreur lors du parsing CSV IA: {exc}") from exc

    @staticmethod
    def _read_csv(file_content: bytes) -> tuple[pd.DataFrame, str]:
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
        last_error: Exception | None = None

        for encoding in encodings:
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
            except Exception as exc:  # pragma: no cover - fallback sequence
                last_error = exc

        raise ValueError(f"Impossible de lire le CSV: {last_error}")

    @staticmethod
    def _build_sample_payload(df: pd.DataFrame) -> dict[str, Any]:
        sample_df = df.head(1)
        rows: list[dict[str, str]] = []

        for _, row in sample_df.iterrows():
            rows.append({str(k): str(v) for k, v in row.to_dict().items()})
        return {"headers": [str(col) for col in df.columns.tolist()], "sample_rows": rows}

    @staticmethod
    def _request_ai_mapping(
        sample_payload: dict[str, Any],
        available_columns: list[str],
        refinement_reason: str | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        if not sample_payload.get("sample_rows"):
            raise ValueError("CSV vide: aucun echantillon a envoyer au modele")

        system_prompt = CsvAiPlanningParser._load_text(
            CsvAiPlanningParser._PROMPTS_DIR / "system_prompt.txt"
        )
        user_template = CsvAiPlanningParser._load_text(
            CsvAiPlanningParser._PROMPTS_DIR / "mapping_prompt_template.txt"
        )
        schema = CsvAiPlanningParser._load_schema()

        user_prompt = CsvAiPlanningParser._build_user_prompt(
            user_template=user_template,
            sample_payload=sample_payload,
            available_columns=available_columns,
            refinement_reason=refinement_reason,
        )
        payload = CsvAiPlanningParser._build_ollama_payload(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
        )

        mapping, _raw_content = CsvAiPlanningParser._call_ollama(payload)

        if "fields" not in mapping:
            raise ValueError("Reponse IA invalide: champ 'fields' manquant")

        logger.debug("CSV IA raw mapping (attempt=%s): %s", attempt, mapping)
        return mapping

    @staticmethod
    def _build_user_prompt(
        user_template: str,
        sample_payload: dict[str, Any],
        available_columns: list[str],
        refinement_reason: str | None = None,
    ) -> str:
        user_prompt = user_template.format(
            sample_payload=json.dumps(sample_payload, ensure_ascii=False, indent=2)
        )
        user_prompt += "\nUtilise uniquement les noms exacts presents dans headers."
        if refinement_reason:
            user_prompt += (
                "\nCorrection demandee: la tentative precedente a echoue avec l'erreur: "
                f"{refinement_reason}\nPropose un mapping corrige."
            )
        return user_prompt

    @staticmethod
    def _build_ollama_payload(system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "model": config.AI_IMPORT_MODEL,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": 0,
                "num_predict": 320,
                "top_p": 0.1,
            },
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "format": schema,
        }

    @staticmethod
    def _call_ollama(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
        response = None
        last_error: Exception | None = None
        for network_attempt in range(2):
            try:
                started = time.perf_counter()
                response = requests.post(
                    f"{config.OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                    timeout=config.OLLAMA_REQUEST_TIMEOUT_S,
                )
                response.raise_for_status()
                logger.info(
                    "CSV IA Ollama call success: attempt=%s elapsed=%.2fs",
                    network_attempt + 1,
                    time.perf_counter() - started,
                )
                break
            except RequestException as exc:
                last_error = exc
                logger.warning(
                    "CSV IA Ollama call failed: attempt=%s elapsed=%.2fs error=%s",
                    network_attempt + 1,
                    time.perf_counter() - started,
                    exc,
                )
                if network_attempt == 0:
                    time.sleep(2)
                    continue
                raise ValueError(f"Echec appel Ollama: {exc}") from exc

        if response is None:
            raise ValueError(f"Echec appel Ollama: {last_error}")

        content = response.json().get("message", {}).get("content", "")
        raw_content = str(content)
        if isinstance(content, dict):
            mapping = content
        else:
            try:
                mapping = CsvAiPlanningParser._parse_json_object(raw_content)
            except Exception:
                logger.warning("CSV IA response invalid JSON, starting repair call. raw_chars=%s", len(raw_content))
                repaired_raw = CsvAiPlanningParser._repair_json_with_ollama(
                    raw_content,
                    payload.get("format", {"type": "object"}),
                )
                mapping = CsvAiPlanningParser._parse_json_object(repaired_raw)
                raw_content = repaired_raw
        return mapping, raw_content

    @staticmethod
    def _repair_json_with_ollama(raw_content: str, schema: dict[str, Any]) -> str:
        repair_prompt = (
            "Corrige ce contenu pour produire un JSON strict valide conforme au schema. "
            "Ne change pas le sens metier. Aucun texte hors JSON.\n\n"
            f"Contenu:\n{raw_content}"
        )
        repair_payload = {
            "model": config.AI_IMPORT_MODEL,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": "Tu es un reparateur JSON strict. Reponds uniquement en JSON valide."},
                {"role": "user", "content": repair_prompt},
            ],
            "options": {"temperature": 0, "num_predict": 320, "top_p": 0.1},
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "format": schema,
        }

        started = time.perf_counter()
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/chat",
            json=repair_payload,
            timeout=config.OLLAMA_REQUEST_TIMEOUT_S,
        )
        response.raise_for_status()
        logger.info("CSV IA Ollama repair success: elapsed=%.2fs", time.perf_counter() - started)
        content = response.json().get("message", {}).get("content", "")
        return str(content)

    @staticmethod
    def _load_text(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Ressource prompt introuvable: {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _load_schema() -> dict[str, Any]:
        schema_path = CsvAiPlanningParser._SCHEMAS_DIR / "mapping_response.schema.json"
        if not schema_path.exists():
            return {"type": "object"}
        return json.loads(schema_path.read_text(encoding="utf-8"))

    @staticmethod
    def _parse_json_object(content: str) -> dict[str, Any]:
        content = content.strip()
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            raise ValueError("Aucun JSON detecte dans la reponse IA")

        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("Le JSON IA n'est pas un objet")
        return parsed

    @staticmethod
    def _build_events(df: pd.DataFrame, mapping: dict[str, Any]) -> tuple[list[Event], float]:
        available_columns = [str(col) for col in df.columns.tolist()]

        fields = mapping.get("fields", {})
        required_targets = ["title", "start_time", "end_time", "location", "description"]

        for target in required_targets:
            if target not in fields:
                raise ValueError(f"Mapping IA incomplet: {target} manquant")

        resolved_fields = CsvAiPlanningParser._resolve_mapping_fields(fields, available_columns)

        events: list[Event] = []
        processed_rows = 0

        for _, row in df.iterrows():
            processed_rows += 1
            row_dict = {str(k): str(v) for k, v in row.to_dict().items()}

            title = CsvAiPlanningParser._extract_text(row_dict, resolved_fields["title"])
            start_time = CsvAiPlanningParser._extract_datetime(row_dict, resolved_fields["start_time"])
            end_time = CsvAiPlanningParser._extract_datetime(row_dict, resolved_fields["end_time"])
            location = CsvAiPlanningParser._extract_text(row_dict, resolved_fields["location"])
            description = CsvAiPlanningParser._extract_text(row_dict, resolved_fields["description"])

            if not title or start_time is None or end_time is None:
                continue
            if end_time <= start_time:
                continue

            events.append(
                Event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    description=description,
                )
            )

        if not events:
            logger.warning("Mapping IA recu sans reconstruction d'evenements. mapping=%s columns=%s", mapping, available_columns)
            raise ValueError("Aucun evenement valide reconstruit depuis le mapping IA")

        success_ratio = len(events) / processed_rows if processed_rows else 0.0
        return events, success_ratio

    @staticmethod
    def _extract_text(row: dict[str, str], spec: dict[str, Any]) -> str:
        mode = str(spec.get("mode", "single"))
        columns = spec.get("columns", []) or []

        if mode == "empty":
            return ""
        if mode == "single" and columns:
            for column in columns:
                value = str(row.get(column, "")).strip()
                if value:
                    return value
            return ""
        if mode == "concat" and columns:
            separator = str(spec.get("separator", " "))
            values = [str(row.get(column, "")).strip() for column in columns]
            return separator.join([value for value in values if value]).strip()
        if mode == "datetime_combine" and len(columns) >= 2:
            left = str(row.get(columns[0], "")).strip()
            right = str(row.get(columns[1], "")).strip()
            return f"{left} {right}".strip()
        return ""

    @staticmethod
    def _extract_datetime(row: dict[str, str], spec: dict[str, Any]) -> datetime | None:
        raw = CsvAiPlanningParser._extract_text(row, spec)
        if not raw:
            return None

        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return None

        return parsed.to_pydatetime()

    @staticmethod
    def _compute_confidence(mapping: dict[str, Any], success_ratio: float) -> float:
        model_conf = float(mapping.get("overall_confidence", 0.0) or 0.0)

        fields = mapping.get("fields", {})
        field_scores: list[float] = []
        for key in ["title", "start_time", "end_time", "location", "description"]:
            field_conf = float(fields.get(key, {}).get("confidence", 0.0) or 0.0)
            field_scores.append(field_conf)
        field_avg = sum(field_scores) / len(field_scores) if field_scores else 0.0

        score = (0.45 * model_conf) + (0.25 * field_avg) + (0.30 * max(0.0, min(1.0, success_ratio)))
        return round(max(0.0, min(1.0, score)), 2)

    @staticmethod
    def _resolve_mapping_fields(fields: dict[str, Any], available_columns: list[str]) -> dict[str, dict[str, Any]]:
        resolved: dict[str, dict[str, Any]] = {}
        for key, spec in fields.items():
            resolved_spec = dict(spec)
            columns = list(spec.get("columns", []) or [])
            mode = str(spec.get("mode", "single"))
            if mode == "single" and len(columns) > 1:
                resolved_spec["columns"] = [columns[0]]

            if mode == "datetime_combine" and len(columns) >= 2 and columns[0] == columns[1]:
                first = CsvAiPlanningParser._resolve_column_name(columns[0], available_columns)
                second = CsvAiPlanningParser._resolve_second_duplicate(columns[1], available_columns, first)
                resolved_spec["columns"] = [first, second]
            else:
                resolved_spec["columns"] = [CsvAiPlanningParser._resolve_column_name(column, available_columns) for column in columns]

            resolved[key] = resolved_spec
        return resolved

    @staticmethod
    def _resolve_second_duplicate(requested: str, available_columns: list[str], first: str) -> str:
        req_norm = CsvAiPlanningParser._normalize_text(requested)
        first_norm = CsvAiPlanningParser._normalize_text(first)

        for candidate in available_columns:
            candidate_norm = CsvAiPlanningParser._normalize_text(candidate)
            if candidate == first:
                continue
            if candidate_norm == req_norm or candidate_norm.startswith(f"{req_norm}.") or candidate_norm.startswith(f"{first_norm}."):
                return candidate
        return CsvAiPlanningParser._resolve_column_name(requested, available_columns)

    @staticmethod
    def _resolve_column_name(requested: str, available_columns: list[str]) -> str:
        if requested in available_columns:
            return requested

        requested_norm = CsvAiPlanningParser._normalize_text(requested)
        direct_by_norm = {CsvAiPlanningParser._normalize_text(col): col for col in available_columns}
        if requested_norm in direct_by_norm:
            return direct_by_norm[requested_norm]

        for col in available_columns:
            col_norm = CsvAiPlanningParser._normalize_text(col)
            if col_norm.startswith(f"{requested_norm}.") or requested_norm.startswith(f"{col_norm}."):
                return col

        return requested

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value))
        ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_only).strip().lower()


csv_ai_planning_parser = CsvAiPlanningParser()
