"""Découpe les PDF, calcule les embeddings et les range dans Qdrant.

    python -m backend.rag.ingest
"""
import uuid
from pathlib import Path

from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from backend.app.core.config import ROOT, settings
from backend.app.core.llm import get_embeddings


def read_pdf_pages(path: Path) -> list[tuple[int, str]]:
    """Renvoie [(numéro de page, texte), …]. On garde la page pour pouvoir la citer."""
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    """Coupe en morceaux de 800 caractères qui se chevauchent de 150.

    Le chevauchement évite de couper une phrase importante en deux sans qu'aucun morceau
    ne la contienne en entier.
    """
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return [c for c in chunks if c.strip()]


def ingest_folder(folder: Path) -> int:
    client = QdrantClient(url=settings.qdrant_url)
    embeddings = get_embeddings()
    dim = len(embeddings.embed_query("test"))            # taille des vecteurs (768 pour nomic-embed-text)
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            settings.qdrant_collection,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

    points = []
    for pdf in sorted(folder.glob("*.pdf")):
        reference = pdf.stem                              # "AO-2026-0001.pdf" -> "AO-2026-0001"
        for page, page_text in read_pdf_pages(pdf):
            chunks = chunk_text(page_text)
            vectors = embeddings.embed_documents(chunks) if chunks else []
            for j, (chunk, vector) in enumerate(zip(chunks, vectors)):
                # Un id STABLE : relancer l'ingestion remplace les points au lieu de les dupliquer.
                point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{reference}-{page}-{j}"))
                points.append(PointStruct(
                    id=point_id, vector=vector,
                    payload={"reference": reference, "page": page, "file": pdf.name, "text": chunk},
                ))
    if points:
        client.upsert(settings.qdrant_collection, points=points)   # upsert = insérer ou remplacer
    print(f"{len(points)} morceaux indexés")
    return len(points)


if __name__ == "__main__":
    ingest_folder(ROOT / "data" / "raw" / "pdfs")