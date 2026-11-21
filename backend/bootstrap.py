"""Prépare les données du projet, en ne faisant QUE ce qui manque (on peut le relancer sans risque).

    python -m backend.bootstrap

Appelé automatiquement par start.bat. Étapes :
  1. attendre PostgreSQL, Qdrant et Ollama ;
  2. télécharger les modèles Ollama s'ils manquent ;
  3. générer les données de démo si besoin, puis les charger en base ;
  4. entraîner le modèle de score s'il n'existe pas ;
  5. calculer les scores s'ils manquent ;
  6. indexer les PDF dans Qdrant si la collection est vide.
"""
import subprocess
import sys
import time

import httpx
from sqlalchemy import text

from backend.app.core.config import ROOT, settings
from backend.app.db.session import engine
from backend.ml.train import MODEL_PATH

PY = sys.executable          # le Python du venv qui exécute ce script


def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def run(*module_and_args: str) -> None:
    """Lance 'python -m <module> <args>' et s'arrête si la commande échoue."""
    print(f"    $ python -m {' '.join(module_and_args)}", flush=True)
    subprocess.run([PY, "-m", *module_and_args], cwd=ROOT, check=True)


def wait_for(name: str, check, timeout: int = 120) -> None:
    """Réessaie 'check()' jusqu'à ce qu'il réussisse (ou abandonne après 'timeout' secondes)."""
    start = time.time()
    while True:
        try:
            check()
            print(f"    {name} : OK")
            return
        except Exception as error:
            if time.time() - start > timeout:
                sys.exit(f"    {name} ne répond pas après {timeout} s ({type(error).__name__}). Arrêt.")
            time.sleep(2)


def postgres_ready() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1 FROM fact_tender LIMIT 1"))


def scalar(sql: str):
    with engine.connect() as conn:
        return conn.execute(text(sql)).scalar()


def main() -> None:
    step("Services")
    wait_for("PostgreSQL", postgres_ready)
    wait_for("Qdrant", lambda: httpx.get(f"{settings.qdrant_url}/readyz", timeout=3).raise_for_status())
    wait_for("Ollama", lambda: httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3).raise_for_status())

    step("Modèles Ollama")
    # Ollama renvoie toujours le nom complet avec son "tag" : "qwen2.5:3b", "nomic-embed-text:latest".
    installed = {m["name"] for m in httpx.get(f"{settings.ollama_base_url}/api/tags").json()["models"]}
    for model in (settings.llm_model, settings.embedding_model):
        full = model if ":" in model else f"{model}:latest"
        if full in installed:
            print(f"    {full} : déjà présent")
        else:
            print(f"    {full} : téléchargement (une seule fois, quelques minutes)…")
            subprocess.run(["ollama", "pull", full], check=True)

    step("Données")
    samples = ROOT / "data" / "samples" / "tenders.jsonl"
    if not samples.exists() or not any((ROOT / "data" / "raw" / "pdfs").glob("*.pdf")):
        run("backend.scraper.generate_samples")
    count = scalar("SELECT COUNT(*) FROM fact_tender")
    if count == 0:
        run("backend.pipeline.run", "--no-llm")
    else:
        print(f"    {count} appels d'offres déjà en base")

    step("Modèle de score")
    if MODEL_PATH.exists():
        print("    modèle déjà entraîné")
    else:
        wait_for("MLflow", lambda: httpx.get(settings.mlflow_tracking_uri, timeout=3).raise_for_status(), timeout=90)
        run("backend.ml.train")

    missing = scalar("SELECT COUNT(*) FROM fact_tender WHERE score IS NULL")
    if missing:
        print(f"    {missing} avis sans score : calcul (10 justifications rédigées par le LLM)…")
        run("backend.ml.score_all", "--limit", "10")
    else:
        print("    tous les avis ont un score")

    step("Index des documents (Qdrant)")
    response = httpx.get(f"{settings.qdrant_url}/collections/{settings.qdrant_collection}")
    points = response.json()["result"]["points_count"] if response.status_code == 200 else 0
    if points:
        print(f"    {points} morceaux déjà indexés")
    else:
        run("backend.rag.ingest")

    print("\nDonnées prêtes.")


if __name__ == "__main__":
    main()
