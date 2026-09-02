#!/usr/bin/env python3
"""Benchmark Ollama models against the CSV AI planning import workflow.

The script intentionally reuses `CsvAiPlanningParser` for the
CSV reading, prompt building, Ollama call, mapping validation and event rebuild.
It only adds the benchmark loop around that existing workflow.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


DEFAULT_MODELS = ["qwen2.5:0.5b-instruct", "qwen3:0.6b", "gemma3:1b"]
RESULTS_DIR = Path(__file__).resolve().parent / "benchmark_results"


def ensure_repo_root_on_path() -> None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend").is_dir() and (parent / "docker" / "docker-compose.ollama.yml").exists():
            sys.path.insert(0, str(parent))
            return


ensure_repo_root_on_path()


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


def cprint(label: str, text: str = "", color: str = Color.CYAN) -> None:
    prefix = f"{Color.BOLD}{color}[{label}]{Color.RESET}"
    print(f"{prefix} {text}" if text else prefix)


def compact_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def ollama_tags(base_url: str, timeout_s: int) -> set[str]:
    response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout_s)
    response.raise_for_status()
    return {str(model.get("name")) for model in response.json().get("models", [])}


def ollama_loaded_models(base_url: str, timeout_s: int) -> list[dict[str, Any]]:
    response = requests.get(f"{base_url.rstrip('/')}/api/ps", timeout=timeout_s)
    response.raise_for_status()
    loaded_models = []
    for model in response.json().get("models", []):
        loaded_models.append(
            {
                "name": model.get("name", ""),
                "size": model.get("size", ""),
                "processor": model.get("processor", ""),
                "until": model.get("expires_at", ""),
            }
        )
    return loaded_models


def pull_model(base_url: str, model: str, timeout_s: int) -> None:
    response = requests.post(
        f"{base_url.rstrip('/')}/api/pull",
        json={"name": model, "stream": False},
        timeout=timeout_s,
    )
    response.raise_for_status()


def md_value(value: object) -> str:
    if value is None:
        return "n/a"
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def build_markdown_report(output: dict[str, Any]) -> str:
    generated_at = output["generated_at"]
    lines = [
        "# Benchmark IA CSV",
        "",
        f"- Date: `{generated_at}`",
        f"- CSV: `{output['csv']}`",
        f"- Ollama: `{output['ollama_base_url']}`",
        f"- Acceleration demandee: `{output['ia_acceleration_mode']}`",
        f"- Repeats: `{output['repeats']}`",
        f"- Modeles: `{', '.join(output['models'])}`",
        "",
        "## Synthese",
        "",
        "| Modele | Reussite | Temps moyen | Temps min | Confiance moyenne |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for result in output["results"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    md_value(result["model"]),
                    f"{result['ok_runs']}/{result['total_runs']}",
                    f"{result['avg_elapsed_s']}s" if result["avg_elapsed_s"] is not None else "n/a",
                    f"{result['min_elapsed_s']}s" if result["min_elapsed_s"] is not None else "n/a",
                    md_value(result["avg_confidence"]),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Details par modele", ""])

    for result in output["results"]:
        lines.extend(
            [
                f"### {result['model']}",
                "",
                "| Run | Statut | Temps | Evenements | Success ratio | Confiance | Detail |",
                "| ---: | --- | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for run in result["runs"]:
            status = "OK" if run["ok"] else "KO"
            detail = run.get("summary") if run["ok"] else run.get("error", "")
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_value(run["run"]),
                        status,
                        f"{run['elapsed_s']}s",
                        md_value(run.get("events")),
                        md_value(run.get("success_ratio")),
                        md_value(run.get("confidence")),
                        md_value(detail),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(["## Modeles charges dans Ollama apres benchmark", ""])
    if output["loaded_models"]:
        lines.extend(
            [
                "| Modele | Taille | Processeur | Expiration |",
                "| --- | ---: | --- | --- |",
            ]
        )
        for model in output["loaded_models"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        md_value(model.get("name")),
                        md_value(model.get("size")),
                        md_value(model.get("processor")),
                        md_value(model.get("until")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("Aucun modele charge au moment de la generation du rapport.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(output: dict[str, Any]) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = RESULTS_DIR / f"benchmark_results_{today}.md"
    report_path.write_text(build_markdown_report(output), encoding="utf-8")
    return report_path


def build_payload(schedule_parser, model: str, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    payload = schedule_parser._build_ollama_payload(system_prompt=system_prompt, user_prompt=user_prompt, schema=schema)
    payload["model"] = model
    return payload


def benchmark_model(
    schedule_parser,
    model: str,
    repeats: int,
    df,
    available_columns: list[str],
    sample_payload: dict[str, Any],
    system_prompt: str,
    user_template: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    user_prompt = schedule_parser._build_user_prompt(
        user_template=user_template,
        sample_payload=sample_payload,
        available_columns=available_columns,
    )
    payload = build_payload(schedule_parser, model, system_prompt, user_prompt, schema)

    runs: list[dict[str, Any]] = []
    for run_index in range(1, repeats + 1):
        started = time.perf_counter()
        try:
            mapping, raw_content = schedule_parser._call_ollama(payload)
            elapsed_s = time.perf_counter() - started
            events, success_ratio = schedule_parser._build_events(df, mapping)
            confidence = schedule_parser._compute_confidence(mapping, success_ratio)
            runs.append(
                {
                    "run": run_index,
                    "ok": True,
                    "elapsed_s": round(elapsed_s, 3),
                    "events": len(events),
                    "success_ratio": round(success_ratio, 3),
                    "confidence": confidence,
                    "summary": str(mapping.get("summary", "")),
                    "raw_chars": len(raw_content),
                }
            )
        except Exception as exc:
            elapsed_s = time.perf_counter() - started
            runs.append({"run": run_index, "ok": False, "elapsed_s": round(elapsed_s, 3), "error": str(exc)})

    ok_runs = [run for run in runs if run["ok"]]
    elapsed_values = [float(run["elapsed_s"]) for run in ok_runs]
    confidence_values = [float(run["confidence"]) for run in ok_runs]

    return {
        "model": model,
        "ok_runs": len(ok_runs),
        "total_runs": repeats,
        "avg_elapsed_s": round(statistics.mean(elapsed_values), 3) if elapsed_values else None,
        "min_elapsed_s": round(min(elapsed_values), 3) if elapsed_values else None,
        "avg_confidence": round(statistics.mean(confidence_values), 3) if confidence_values else None,
        "runs": runs,
    }


def main() -> int:
    try:
        from backend.core.config import config
        from backend.services.planning_import_services.csv_ai import CsvAiPlanningParser
    except ModuleNotFoundError as exc:
        cprint("ERROR", f"Dependance Python manquante: {exc}", Color.RED)
        return 10

    cli = argparse.ArgumentParser(description="Benchmark CSV IA mapping models through Ollama")
    cli.add_argument(
        "csv_path",
        nargs="?",
        default="backend/services/planning_import_services/csv_ai/debug/CNAM_Planning_18122025024326_158904.csv",
    )
    cli.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="Modeles Ollama a comparer")
    cli.add_argument("--repeats", type=int, default=3, help="Nombre de runs par modele")
    cli.add_argument("--pull", action="store_true", help="Telecharger les modeles absents avant benchmark")
    cli.add_argument("--json", action="store_true", help="Afficher uniquement le resultat JSON")
    args = cli.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        cprint("ERROR", f"CSV introuvable: {csv_path}", Color.RED)
        return 1

    df, encoding = CsvAiPlanningParser._read_csv(csv_path.read_bytes())
    available_columns = [str(col) for col in df.columns.tolist()]
    sample_payload = CsvAiPlanningParser._build_sample_payload(df)
    system_prompt = CsvAiPlanningParser._load_text(
        CsvAiPlanningParser._PROMPTS_DIR / "system_prompt.txt"
    )
    user_template = CsvAiPlanningParser._load_text(
        CsvAiPlanningParser._PROMPTS_DIR / "mapping_prompt_template.txt"
    )
    schema = CsvAiPlanningParser._load_schema()

    base_url = config.OLLAMA_BASE_URL
    timeout_s = config.OLLAMA_REQUEST_TIMEOUT_S

    if not args.json:
        cprint("START", f"Benchmark CSV IA - {csv_path}", Color.GREEN)
        cprint("INFO", f"Ollama: {base_url} | encoding={encoding} | rows={len(df.index)} | columns={len(available_columns)}")
        cprint("INFO", f"Prompt sample compact: {len(compact_json(sample_payload))} chars")

    available_models = ollama_tags(base_url, timeout_s)
    missing_models = [model for model in args.models if model not in available_models]
    if missing_models and not args.pull:
        cprint("ERROR", f"Modeles absents: {', '.join(missing_models)}. Relance avec --pull.", Color.RED)
        return 2

    for model in missing_models:
        if not args.json:
            cprint("PULL", model, Color.YELLOW)
        pull_model(base_url, model, timeout_s)

    results = []
    for model in args.models:
        if not args.json:
            cprint("MODEL", model, Color.YELLOW)
        result = benchmark_model(
            schedule_parser=CsvAiPlanningParser,
            model=model,
            repeats=max(1, args.repeats),
            df=df,
            available_columns=available_columns,
            sample_payload=sample_payload,
            system_prompt=system_prompt,
            user_template=user_template,
            schema=schema,
        )
        results.append(result)
        if not args.json:
            avg_elapsed = f"{result['avg_elapsed_s']}s" if result["avg_elapsed_s"] is not None else "n/a"
            avg_confidence = result["avg_confidence"] if result["avg_confidence"] is not None else "n/a"
            cprint(
                "RESULT",
                f"ok={result['ok_runs']}/{result['total_runs']} avg={avg_elapsed} confidence={avg_confidence}",
                Color.GREEN if result["ok_runs"] else Color.RED,
            )

    try:
        loaded_models = ollama_loaded_models(base_url, timeout_s)
    except Exception as exc:
        loaded_models = [{"name": "Erreur lecture /api/ps", "size": "", "processor": str(exc), "until": ""}]

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "csv": str(csv_path),
        "ollama_base_url": base_url,
        "ia_acceleration_mode": os.getenv("IA_ACCELERATION_MODE", "unknown"),
        "repeats": max(1, args.repeats),
        "models": args.models,
        "loaded_models": loaded_models,
        "results": results,
    }
    report_path = write_markdown_report(output)
    if not args.json:
        cprint("REPORT", str(report_path), Color.GREEN)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if all(result["ok_runs"] for result in results) else 3


if __name__ == "__main__":
    raise SystemExit(main())
