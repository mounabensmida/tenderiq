"""Point d'entrée de l'API :  uvicorn backend.app.main:app --reload"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from backend.app.api.routes import router

app = FastAPI(title="TenderIQ API", version="0.1.0",
            description="Veille et analyse d'appels d'offres : score explicable, RAG, Text-to-SQL, agent.")

# CORS : autorise le front (un AUTRE port = une autre "origine") à appeler l'API depuis le navigateur.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

# Ajoute /metrics : nombre de requêtes, durées, codes d'erreur… au format Prometheus.
Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "ok"}