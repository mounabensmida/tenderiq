"""Calcule le score, les raisons SHAP et la justification LLM de chaque appel d'offres.

    python -m backend.ml.score_all --limit 20     # justification LLM pour les 20 premiers
    python -m backend.ml.score_all --no-llm       # scores + raisons seulement (rapide)
"""
import argparse
import json

from sqlalchemy import text

from backend.app.core.llm import get_llm
from backend.app.db.session import engine
from backend.ml.explain import ScoreExplainer, load_model
from backend.ml.features import build_features, load_tenders

JUSTIFY_PROMPT = """Un appel d'offres intitulé « <<TITRE>> » a un score de pertinence de <<SCORE>> %.
Les facteurs qui ont le plus pesé sont :
<<RAISONS>>
Explique en 2 phrases simples, à un commercial, pourquoi ce score. N'invente aucun autre facteur."""


def justify(title: str, score: float, reasons: list[dict]) -> str:
    lines = "\n".join(f"- {r['label']} ({r['direction']} le score)" for r in reasons)
    prompt = (JUSTIFY_PROMPT.replace("<<TITRE>>", title)
              .replace("<<SCORE>>", f"{score * 100:.0f}").replace("<<RAISONS>>", lines))
    return get_llm().invoke(prompt).content.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20, help="nombre de justifications LLM")
    parser.add_argument("--no-llm", action="store_true")
    args = parser.parse_args()

    df = load_tenders()
    X = build_features(df)
    scorer = ScoreExplainer(load_model())
    scores = scorer.score(X)

    with engine.begin() as conn:
        for i, (idx, row) in enumerate(df.iterrows()):
            reasons = scorer.explain(X.loc[[idx]])          # [[idx]] garde un tableau d'une ligne
            justification = None
            if not args.no_llm and i < args.limit:
                justification = justify(row["title"], scores[i], reasons)
                print(f"{row['reference']} {scores[i]:.0%} -> {justification[:80]}…")
            conn.execute(text("""UPDATE fact_tender
                                SET score = :s, score_reasons = CAST(:r AS JSONB),
                                    justification = COALESCE(:j, justification)
                                WHERE tender_id = :id"""),
                        {"s": scores[i], "r": json.dumps(reasons, ensure_ascii=False),
                        "j": justification, "id": int(row["tender_id"])})
    print(f"{len(df)} appels d'offres notés")


if __name__ == "__main__":
    main()