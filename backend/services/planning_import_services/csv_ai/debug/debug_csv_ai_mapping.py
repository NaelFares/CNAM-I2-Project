#!/usr/bin/env python3
"""
Script de debug pour le workflow CSV IA.

Reproduit exactement le pipeline du parser backend et affiche chaque étape :
  1. Lecture CSV
  2. Chargement des prompts et du schéma
  3. Appel au fournisseur IA (Ollama ou Groq)
  4. Reconstruction des événements

Usage (dans le conteneur backend) :
  python debug_csv_ai_mapping.py <chemin_csv>
  python debug_csv_ai_mapping.py <chemin_csv> --quiet
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path


# ── Couleurs terminal ──────────────────────────────────────────────────────────

class Color:
    RESET = "\033[0m"; BOLD = "\033[1m"
    CYAN = "\033[36m"; GREEN = "\033[32m"; YELLOW = "\033[33m"
    RED = "\033[31m";  MAGENTA = "\033[35m"


def cprint(label: str, text: str = "", color: str = Color.CYAN) -> None:
    print(f"{Color.BOLD}{color}[{label}]{Color.RESET}" + (f" {text}" if text else ""))


def dump_json(label: str, data: object) -> None:
    cprint(label, color=Color.MAGENTA)
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ── Chronomètre live ───────────────────────────────────────────────────────────

def _fmt(seconds: float) -> str:
    s = max(0, int(seconds))
    return f"{s // 60}m {s % 60:02d}s" if s >= 60 else f"{s}s"


def start_timer(label: str, started: float) -> threading.Event:
    stop = threading.Event()
    def tick():
        while not stop.wait(1):
            sys.stdout.write(f"\r{Color.BOLD}{Color.CYAN}[{label}]{Color.RESET} Temps ecoule: {_fmt(time.perf_counter() - started)}")
            sys.stdout.flush()
    threading.Thread(target=tick, daemon=True).start()
    return stop


def stop_timer(stop: threading.Event, label: str, started: float) -> None:
    stop.set()
    sys.stdout.write(f"\r{Color.BOLD}{Color.GREEN}[{label}]{Color.RESET} Temps ecoule: {_fmt(time.perf_counter() - started)}\n")
    sys.stdout.flush()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        from backend.services.planning_import_services.csv_ai import CsvAiPlanningParser
        from backend.services.planning_import_services.csv_ai.providers import get_provider
        from backend.core.config import config
    except ModuleNotFoundError as exc:
        cprint("ERROR", f"Dependance manquante : {exc}. Installe les deps backend (backend/requirements.txt).", Color.RED)
        return 10

    cli = argparse.ArgumentParser(description="Debug CSV IA mapping")
    cli.add_argument("csv_path", nargs="?", default="backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv")
    cli.add_argument("--quiet", action="store_true", help="Masquer les prompts et la reponse brute")
    args = cli.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        cprint("ERROR", f"CSV introuvable : {csv_path}", Color.RED)
        return 1

    cprint("START", "Debug workflow CSV IA", Color.GREEN)
    cprint("FILE", str(csv_path))

    # Étape 1 : lecture CSV
    cprint("STEP 1", "Lecture CSV")
    try:
        df, encoding = CsvAiPlanningParser._read_csv(csv_path.read_bytes())
    except Exception as exc:
        cprint("ERROR", f"Lecture impossible : {exc}", Color.RED)
        return 2

    available_columns = [str(col) for col in df.columns.tolist()]
    sample_payload = CsvAiPlanningParser._build_sample_payload(df)
    cprint("INFO", f"Encodage : {encoding}  |  Lignes : {len(df.index)}  |  Colonnes : {len(available_columns)}")
    dump_json("COLUMNS", available_columns)
    dump_json("SAMPLE PAYLOAD", sample_payload)

    # Étape 2 : chargement des ressources
    cprint("STEP 2", "Chargement prompts et schema")
    system_prompt = CsvAiPlanningParser._load_text(CsvAiPlanningParser._PROMPTS_DIR / "system_prompt.txt")
    user_template = CsvAiPlanningParser._load_text(CsvAiPlanningParser._PROMPTS_DIR / "mapping_prompt_template.txt")
    schema = CsvAiPlanningParser._load_schema()

    cprint("INFO", f"Fournisseur : {config.AI_IMPORT_PROVIDER}  |  Modele : {config.AI_IMPORT_MODEL}")
    if config.AI_IMPORT_PROVIDER == "groq":
        cprint("INFO", f"Cle Groq : {'OK' if config.GROQ_API_KEY else 'MANQUANTE'}")
    else:
        cprint("INFO", f"Ollama URL : {config.OLLAMA_BASE_URL}  |  Timeout : {config.OLLAMA_REQUEST_TIMEOUT_S}s")

    if not args.quiet:
        cprint("SYSTEM PROMPT", color=Color.YELLOW)
        print(system_prompt)

    # Étape 3 : appel IA (2 tentatives)
    cprint("STEP 3", "Appel IA (max 2 tentatives)")
    provider = get_provider()
    provider_label = config.AI_IMPORT_PROVIDER.upper()
    last_error: Exception | None = None

    for attempt in range(1, 3):
        cprint("ATTEMPT", f"Tentative {attempt}/2", Color.YELLOW)
        user_prompt = CsvAiPlanningParser._build_user_prompt(
            user_template=user_template,
            sample_payload=sample_payload,
            available_columns=available_columns,
            refinement_reason=str(last_error) if last_error else None,
        )
        if not args.quiet:
            cprint("USER PROMPT", color=Color.YELLOW)
            print(user_prompt)

        started = time.perf_counter()
        timer_stop = start_timer(f"{provider_label} TIMER", started)
        try:
            mapping = provider.call(system_prompt, user_prompt, schema)
        except Exception as exc:
            stop_timer(timer_stop, f"{provider_label} TIMER", started)
            last_error = exc
            cprint(f"{provider_label} ERROR", str(exc), Color.RED)
            continue
        stop_timer(timer_stop, f"{provider_label} TIMER", started)
        cprint("INFO", f"Temps inference : {time.perf_counter() - started:.2f}s", Color.GREEN)

        dump_json("MAPPING RECU", mapping)
        resolved = CsvAiPlanningParser._resolve_mapping_fields(mapping.get("fields", {}), available_columns)
        dump_json("MAPPING RESOLU", resolved)

        # Étape 4 : reconstruction des événements
        cprint("STEP 4", "Reconstruction des evenements")
        try:
            events, success_ratio = CsvAiPlanningParser._build_events(df, mapping)
            confidence = CsvAiPlanningParser._compute_confidence(mapping, success_ratio)
        except Exception as exc:
            last_error = exc
            cprint("BUILD ERROR", str(exc), Color.RED)
            continue

        cprint("SUCCESS", "Mapping exploitable", Color.GREEN)
        cprint("INFO", f"Evenements : {len(events)}  |  Ratio : {success_ratio:.2f}  |  Confiance : {confidence:.2f}")
        cprint("INFO", f"Revue requise : {confidence < 0.80}")
        dump_json("EVENTS PREVIEW (max 3)", [e.to_dict() for e in events[:3]])
        return 0

    cprint("FAILED", f"Echec apres 2 tentatives : {last_error}", Color.RED)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
