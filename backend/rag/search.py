"""Recherche hybride : sens (vecteurs) + mots exacts, fusionnés par RRF."""
import re

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from backend.app.core.config import settings
from backend.app.core.llm import get_embeddings

REFERENCE_PATTERN = re.compile(r"AO-\d{4}-\d{4}")       # format des références de nos avis


class HybridRetriever:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url)
        self.embeddings = get_embeddings()

    def vector_search(self, question: str, k: int, reference: str | None):
        query_filter = None
        if reference:                                     # on ne cherche que dans ce document
            query_filter = Filter(must=[FieldCondition(key="reference", match=MatchValue(value=reference))])
        result = self.client.query_points(
            settings.qdrant_collection,
            query=self.embeddings.embed_query(question),
            query_filter=query_filter,
            limit=k,
            with_payload=True,
        )
        return result.points

    @staticmethod
    def keyword_score(question: str, passage: str) -> int:
        """Nombre de mots de la question (4 lettres ou plus) présents dans le passage."""
        words = set(re.findall(r"\w{4,}", question.lower()))
        passage = passage.lower()
        return sum(1 for w in words if w in passage)

    def search(self, question: str, k: int = 4) -> list:
        match = REFERENCE_PATTERN.search(question)
        hits = self.vector_search(question, k=15, reference=match.group(0) if match else None)
        vec_rank = {h.id: rank for rank, h in enumerate(hits)}
        by_keywords = sorted(hits, key=lambda h: self.keyword_score(question, h.payload["text"]), reverse=True)
        kw_rank = {h.id: rank for rank, h in enumerate(by_keywords)}
        # RRF : score = 1/(60 + rang vecteur) + 1/(60 + rang mots-clés). 60 est la constante habituelle.
        fused = sorted(hits, key=lambda h: 1 / (60 + vec_rank[h.id]) + 1 / (60 + kw_rank[h.id]), reverse=True)
        return fused[:k]