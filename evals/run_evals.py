"""Évalue le RAG et le Text-to-SQL. Code de sortie 1 si un score est sous son seuil.

    python -m evals.run_evals
"""
import json
import re
import sys
from decimal import Decimal

from sqlalchemy import text

from backend.agent.sql_tool import run_sql
from backend.app.core.config import ROOT, settings
from backend.app.db.session import readonly_engine
from backend.rag.answer import answer_question


def normalize(s: str) -> str:
    return re.sub(r"\s+", "", str(s).lower())          # "ISO 9001" et "iso9001" deviennent égaux


def eval_rag() -> float:
    data = json.loads((ROOT / "evals" / "rag" / "dataset.json").read_text(encoding="utf-8"))
    scores = []
    for item in data:
        result = answer_question(item["question"])
        found = [normalize(k) in normalize(result["answer"]) for k in item["expected_keywords"]]
        keyword_score = sum(found) / len(found)                       # la bonne info est-elle dans la réponse ?
        cited = any(s["reference"] == item["expected_reference"] and s["page"] == item["expected_page"]
                    for s in result["sources"])                       # la bonne page est-elle citée ?
        score = 0.5 * keyword_score + 0.5 * cited
        scores.append(score)
        print(f"  RAG {score:.2f} | {item['question'][:70]}")
    return sum(scores) / len(scores)


def signature(rows: list[dict]) -> list:
    """Résultat -> forme comparable : on ignore les noms de colonnes, l'ordre et les petits arrondis."""
    out = []
    for row in rows:
        values = []
        for v in row.values():
            if isinstance(v, (int, float, Decimal)):
                values.append(str(round(float(v))))
            else:
                values.append(str(v).strip().lower())
        out.append(tuple(sorted(values)))
    return sorted(out)


def eval_sql() -> float:
    data = json.loads((ROOT / "evals" / "sql" / "dataset.json").read_text(encoding="utf-8"))
    correct = 0
    for item in data:
        with readonly_engine.connect() as conn:
            gold = [dict(r) for r in conn.execute(text(item["gold_sql"])).mappings().all()]
        try:
            ok = signature(run_sql(item["question"])["rows"]) == signature(gold)
        except Exception as error:                      # SQL invalide, refusé, etc. = faux
            ok = False
            print(f"    erreur : {type(error).__name__}")
        correct += ok
        print(f"  SQL {'✓' if ok else '✗'} | {item['question']}")
    return correct / len(data)


def main():
    rag, sql = eval_rag(), eval_sql()
    report = {"rag_score": round(rag, 3), "rag_min": settings.eval_rag_min_score,
            "sql_accuracy": round(sql, 3), "sql_min": settings.eval_sql_min_accuracy}
    (ROOT / "evals" / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if rag < settings.eval_rag_min_score or sql < settings.eval_sql_min_accuracy:
        print("❌ Qualité insuffisante : déploiement bloqué")
        sys.exit(1)
    print("✅ Qualité suffisante")


if __name__ == "__main__":
    main()