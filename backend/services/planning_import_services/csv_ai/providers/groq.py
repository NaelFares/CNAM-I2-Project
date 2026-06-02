"""Fournisseur Groq — appelle l'API cloud Groq (gratuite, très rapide)."""
from __future__ import annotations

import logging
import time
from typing import Any

from backend.core.config import config
from . import parse_json_response

logger = logging.getLogger(__name__)


class GroqProvider:
    """Appelle l'API Groq pour produire le mapping CSV (~1 seconde, gratuit)."""

    def call(self, system_prompt: str, user_prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        from groq import Groq  # lazy : package requis seulement si AI_IMPORT_PROVIDER=groq
        client = Groq(api_key=config.GROQ_API_KEY)
        started = time.perf_counter()
        response = client.chat.completions.create(
            model=config.AI_IMPORT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=320,
        )
        logger.info("Groq call success: elapsed=%.2fs", time.perf_counter() - started)
        return parse_json_response(response.choices[0].message.content or "")
