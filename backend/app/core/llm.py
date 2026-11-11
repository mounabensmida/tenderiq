"""Fabrique les objets LLM et embeddings utilisés partout dans le projet."""
from langchain_ollama import ChatOllama, OllamaEmbeddings

from backend.app.core.config import settings

def get_llm(json_mode: bool = False) -> ChatOllama:
    """Renvoie un LLM prêt à l'emploi.
    json_mode=True oblige le modèle à répondre avec du JSON valide :
    indispensable quand on veut ensuite lire la réponse avec Pydantic.
    """
    return ChatOllama(
    model=settings.llm_model,
    base_url=settings.ollama_base_url,
    temperature=0, # 0 = réponses stables et reproductibles
    format="json" if json_mode else None,
    )
def get_embeddings() -> OllamaEmbeddings:
    """Renvoie le modèle qui transforme un texte en vecteur de nombres."""
    return OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_base_url)