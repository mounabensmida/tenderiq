"""Branche Langfuse (si les clés sont renseignées) pour tracer chaque appel au LLM."""
from functools import lru_cache

from backend.app.core.config import settings


@lru_cache
def get_callbacks() -> list:
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return []                                    # pas de clés -> pas de traçage, l'appli marche quand même
    from langfuse import Langfuse
    from langfuse.langchain import CallbackHandler
    Langfuse(public_key=settings.langfuse_public_key, secret_key=settings.langfuse_secret_key,
             host=settings.langfuse_host)            # initialise le client une fois
    return [CallbackHandler(public_key=settings.langfuse_public_key)]
