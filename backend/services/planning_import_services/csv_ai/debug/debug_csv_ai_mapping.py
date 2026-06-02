#!/usr/bin/env python3
"""Debug runner aligned with backend CSV IA workflow (same parser resources + same logic)."""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path
import requests
from requests import RequestException


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"


def cprint(label: str, text: str = "", color: str = Color.CYAN) -> None:
    prefix = f"{Color.BOLD}{color}[{label}]{Color.RESET}"
    if text:
        print(f"{prefix} {text}")
    else:
        print(prefix)


def dump_json(label: str, payload: object) -> None:
    cprint(label, color=Color.MAGENTA)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def format_elapsed(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60
    if minutes:
        return f"{minutes}m {remaining_seconds:02d}s"
    return f"{remaining_seconds}s"


def start_live_timer(label: str, started: float) -> threading.Event:
    stop_event = threading.Event()

    def tick() -> None:
        while not stop_event.wait(1):
            elapsed = time.perf_counter() - started
            sys.stdout.write(f"\r{Color.BOLD}{Color.CYAN}[{label}]{Color.RESET} Temps ecoule: {format_elapsed(elapsed)}")
            sys.stdout.flush()

    thread = threading.Thread(target=tick, daemon=True)
    thread.start()
    return stop_event


def stop_live_timer(stop_event: threading.Event, label: str, started: float) -> None:
    stop_event.set()
    elapsed = time.perf_counter() - started
    sys.stdout.write(f"\r{Color.BOLD}{Color.GREEN}[{label}]{Color.RESET} Temps ecoule: {format_elapsed(elapsed)}\n")
    sys.stdout.flush()


def call_ollama_with_raw_logs(schedule_parser, payload: dict, base_url: str, timeout_s: int) -> tuple[dict, str]:
    """Same request flow as backend, but always returns raw content for debug visibility."""
    response = None
    last_error: Exception | None = None
    for network_attempt in range(2):
        try:
            response = requests.post(
                f"{base_url.rstrip('/')}/api/chat",
                json=payload,
                timeout=timeout_s,
            )
            response.raise_for_status()
            break
        except RequestException as exc:
            last_error = exc
            if network_attempt == 0:
                time.sleep(2)
                continue
            raise ValueError(f"Echec appel Ollama: {exc}") from exc

    if response is None:
        raise ValueError(f"Echec appel Ollama: {last_error}")

    content = response.json().get("message", {}).get("content", "")
    raw_content = str(content)
    if isinstance(content, dict):
        return content, raw_content
    try:
        mapping = schedule_parser._parse_json_object(raw_content)
    except Exception as exc:
        try:
            repaired_raw = schedule_parser._repair_json_with_ollama(raw_content, payload.get("format", {"type": "object"}))
            repaired_mapping = schedule_parser._parse_json_object(str(repaired_raw))
            combined_raw = (
                "=== RAW MODELE (INVALIDE) ===\n"
                f"{raw_content}\n\n=== RAW REPARE ===\n{repaired_raw}"
            )
            return repaired_mapping, combined_raw
        except Exception:
            raise ValueError(f"JSON modele invalide: {exc}\nRAW_CONTENT:\n{raw_content}") from exc
    return mapping, raw_content


def main() -> int:
    try:
        from backend.services.planning_import_services.csv_ai import CsvAiPlanningParser
    except ModuleNotFoundError as exc:
        cprint(
            "ERROR",
            f"Dependance Python manquante: {exc}. Installe les deps backend (requirements.txt) pour executer ce script en local.",
            Color.RED,
        )
        return 10

    cli = argparse.ArgumentParser(description="Debug CSV IA mapping with backend-equivalent workflow")
    cli.add_argument(
        "csv_path",
        nargs="?",
        default="backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv",
    )
    cli.add_argument("--quiet", action="store_true", help="Masquer le detail prompts/payload/reponse brute")
    args = cli.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        cprint("ERROR", f"CSV introuvable: {csv_path}", Color.RED)
        return 1

    cprint("START", "Debug workflow CSV IA (meme pipeline que backend)", Color.GREEN)
    cprint("FILE", str(csv_path))

    file_content = csv_path.read_bytes()

    # Etape 1: lecture CSV identique au backend
    cprint("STEP 1", "Lecture CSV avec fallback d'encodage backend")
    try:
        df, encoding = CsvAiPlanningParser._read_csv(file_content)
    except Exception as exc:
        cprint("ERROR", f"Lecture CSV impossible: {exc}", Color.RED)
        return 2

    available_columns = [str(col) for col in df.columns.tolist()]
    sample_payload = CsvAiPlanningParser._build_sample_payload(df)

    cprint("INFO", f"Encoding detecte: {encoding}")
    cprint("INFO", f"Nombre de lignes CSV: {len(df.index)}")
    cprint("INFO", f"Nombre de colonnes: {len(available_columns)}")
    dump_json("COLUMNS", available_columns)
    dump_json("SAMPLE PAYLOAD", sample_payload)

    # Etape 2: chargement ressources identiques backend
    cprint("STEP 2", "Chargement prompts et schema depuis ressources backend")
    system_prompt = CsvAiPlanningParser._load_text(
        CsvAiPlanningParser._PROMPTS_DIR / "system_prompt.txt"
    )
    user_template = CsvAiPlanningParser._load_text(
        CsvAiPlanningParser._PROMPTS_DIR / "mapping_prompt_template.txt"
    )
    schema = CsvAiPlanningParser._load_schema()

    cprint("INFO", f"Prompt system length: {len(system_prompt)}")
    cprint("INFO", f"Prompt template length: {len(user_template)}")
    cprint("INFO", f"Schema keys: {list(schema.keys())}")
    from backend.core.config import config
    cprint("INFO", f"Ollama base URL: {config.OLLAMA_BASE_URL}")
    cprint("INFO", f"Modele: {config.AI_IMPORT_MODEL}")
    cprint("INFO", f"Timeout: {config.OLLAMA_REQUEST_TIMEOUT_S}s | Keep-alive: {config.OLLAMA_KEEP_ALIVE}")

    if not args.quiet:
        cprint("SYSTEM PROMPT", color=Color.YELLOW)
        print(system_prompt)

    # Etape 3: workflow 2 tentatives identique backend
    cprint("STEP 3", "Execution des tentatives IA (max=2) comme parser backend")
    last_error: Exception | None = None
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        cprint("ATTEMPT", f"Tentative {attempt}/{max_attempts}", Color.YELLOW)
        refinement_reason = str(last_error) if last_error else None

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

        if not args.quiet:
            cprint("USER PROMPT", color=Color.YELLOW)
            print(user_prompt)

        if not args.quiet:
            cprint("HTTP REQUEST", color=Color.YELLOW)
            print(f"POST {config.OLLAMA_BASE_URL.rstrip('/')}/api/chat")
            dump_json("OLLAMA PAYLOAD", payload)

        started = time.perf_counter()
        timer_stop = start_live_timer("OLLAMA TIMER", started)
        try:
            mapping, raw_content = call_ollama_with_raw_logs(
                schedule_parser=CsvAiPlanningParser,
                payload=payload,
                base_url=config.OLLAMA_BASE_URL,
                timeout_s=config.OLLAMA_REQUEST_TIMEOUT_S,
            )
        except Exception as exc:
            stop_live_timer(timer_stop, "OLLAMA TIMER", started)
            last_error = exc
            cprint("OLLAMA ERROR", str(exc), Color.RED)
            continue
        stop_live_timer(timer_stop, "OLLAMA TIMER", started)
        elapsed = time.perf_counter() - started
        cprint("INFO", f"Temps inference: {elapsed:.2f}s", Color.GREEN)

        if not args.quiet:
            cprint("RAW MODEL CONTENT", color=Color.YELLOW)
            print(raw_content)

        dump_json("MAPPING RECU", mapping)
        for target, spec in (mapping.get("fields", {}) or {}).items():
            if isinstance(spec, dict) and spec.get("mode") == "single" and len(spec.get("columns", []) or []) > 1:
                cprint(
                    "WARNING",
                    f"{target}: mode single avec {len(spec.get('columns', []) or [])} colonnes; le parser utilisera la premiere.",
                    Color.YELLOW,
                )
        resolved_mapping = CsvAiPlanningParser._resolve_mapping_fields(mapping.get("fields", {}), available_columns)
        dump_json("MAPPING RESOLU (SI VALIDE)", resolved_mapping)

        # Etape 4: reconstruction events identique backend
        cprint("STEP 4", "Reconstruction des evenements depuis mapping")
        try:
            events, success_ratio = CsvAiPlanningParser._build_events(df, mapping)
            confidence = CsvAiPlanningParser._compute_confidence(mapping, success_ratio)
            requires_review = confidence < 0.80
        except Exception as exc:
            last_error = exc
            cprint("BUILD ERROR", str(exc), Color.RED)
            continue

        cprint("SUCCESS", "Mapping exploitable reconstruit", Color.GREEN)
        cprint("INFO", f"Events reconstruits: {len(events)}")
        cprint("INFO", f"Success ratio: {success_ratio:.2f}")
        cprint("INFO", f"Confidence score: {confidence:.2f}")
        cprint("INFO", f"Requires user review: {requires_review}")

        preview = [event.to_dict() for event in events[:3]]
        dump_json("EVENTS PREVIEW (max 3)", preview)
        return 0

    cprint("FAILED", f"Echec apres {max_attempts} tentatives: {last_error}", Color.RED)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
