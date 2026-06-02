"""Fournisseur Ollama — appelle un modèle local via l'API Ollama."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from requests import RequestException

from backend.core.config import config
from . import parse_json_response

logger = logging.getLogger(__name__)


class OllamaProvider:
    """Appelle une instance Ollama locale pour produire le mapping CSV."""

    def call(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        payload = self._build_payload(system_prompt, user_prompt, schema)
        raw = self._send(payload)
        if isinstance(raw, dict):
            return raw
        try:
            return parse_json_response(raw)
        except Exception:
            logger.warning("Ollama JSON invalide, tentative de reparation. raw_chars=%s", len(raw))
            repaired = self._repair(raw, schema)
            return parse_json_response(repaired)

    def _build_payload(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "model": config.AI_IMPORT_MODEL,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0, "num_predict": 320, "top_p": 0.1},
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "format": schema,
        }

    def _send(self, payload: dict[str, Any]) -> dict[str, Any] | str:
        url = f"{config.OLLAMA_BASE_URL}/api/chat"
        for attempt in range(2):
            try:
                started = time.perf_counter()
                response = requests.post(url, json=payload, timeout=config.OLLAMA_REQUEST_TIMEOUT_S)
                response.raise_for_status()
                logger.info("Ollama call success: attempt=%s elapsed=%.2fs", attempt + 1, time.perf_counter() - started)
                content = response.json().get("message", {}).get("content", "")
                return content if isinstance(content, dict) else str(content)
            except RequestException as exc:
                logger.warning("Ollama call failed: attempt=%s error=%s", attempt + 1, exc)
                if attempt == 0:
                    time.sleep(2)
                    continue
                raise ValueError(f"Echec appel Ollama: {exc}") from exc
        raise ValueError("Echec appel Ollama: max tentatives atteint")

    def _repair(self, raw: str, schema: dict[str, Any]) -> str:
        """Second appel Ollama pour corriger un JSON malformé."""
        payload = {
            "model": config.AI_IMPORT_MODEL,
            "stream": False,
            "think": False,
            "messages": [
                {"role": "system", "content": "Tu es un reparateur JSON strict. Reponds uniquement en JSON valide."},
                {"role": "user", "content": f"Corrige ce contenu en JSON valide conforme au schema. Aucun texte hors JSON.\n\nContenu:\n{raw}"},
            ],
            "options": {"temperature": 0, "num_predict": 320, "top_p": 0.1},
            "keep_alive": config.OLLAMA_KEEP_ALIVE,
            "format": schema,
        }
        started = time.perf_counter()
        response = requests.post(f"{config.OLLAMA_BASE_URL}/api/chat", json=payload, timeout=config.OLLAMA_REQUEST_TIMEOUT_S)
        response.raise_for_status()
        logger.info("Ollama repair success: elapsed=%.2fs", time.perf_counter() - started)
        return str(response.json().get("message", {}).get("content", ""))
