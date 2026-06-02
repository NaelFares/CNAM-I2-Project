"""
Fournisseurs IA pour le mapping de colonnes CSV.

Deux implémentations disponibles :
- OllamaProvider  : modèle local via une instance Ollama (pas besoin d'internet)
- GroqProvider    : API cloud Groq, gratuite et très rapide (recommandé)

Le fournisseur actif est choisi par la variable d'environnement AI_IMPORT_PROVIDER.
"""
from __future__ import annotations

import json
import re
from typing import Any

from backend.core.config import config


def get_provider():
    """Retourne le fournisseur IA configuré (Ollama ou Groq)."""
    if config.AI_IMPORT_PROVIDER == "groq":
        from .groq import GroqProvider
        return GroqProvider()
    from .ollama import OllamaProvider
    return OllamaProvider()


def parse_json_response(content: str) -> dict[str, Any]:
    """Extrait un objet JSON depuis la réponse brute du modèle."""
    content = content.strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", content)
    if not match:
        raise ValueError("Aucun JSON détecté dans la réponse IA")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Le JSON IA n'est pas un objet")
    return parsed
