"""Question en français -> SQL vérifié -> résultat -> phrase de réponse."""
import json
import re
from decimal import Decimal

from sqlalchemy import text

from backend.app.core.llm import get_llm
from backend.app.db.session import readonly_engine

SCHEMA = """Tables PostgreSQL (schéma en étoile) :
fact_tender(tender_id, reference, title, description, language, budget_tnd, buyer_id, sector_id, country_id,
            source_id, publication_date_id, deadline_date_id, is_relevant, score, justification)
dim_buyer(buyer_id, name)
dim_sector(sector_id, name)   -- valeurs : informatique, telecom, etudes, btp, sante, energie, autre
dim_country(country_id, name) -- ex. 'Tunisie', 'Maroc', 'Sénégal'
dim_date(date_id, full_date, year, month, day, weekday)
Jointures : fact_tender.sector_id = dim_sector.sector_id (idem pour buyer, country) ;
            fact_tender.publication_date_id = dim_date.date_id
budget_tnd est en dinars tunisiens. score est entre 0 et 1."""

SQL_PROMPT = """Tu écris UNE requête SQL PostgreSQL en lecture seule (SELECT) qui répond à la question.
<<SCHEMA>>
Réponds uniquement avec le SQL, sans explication et sans ```.
Question : <<QUESTION>>
SQL :"""

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|execute|call|pg_sleep)\b",
    re.IGNORECASE,
)


class UnsafeSQLError(ValueError):
    """Levée quand une requête générée est refusée par nos contrôles."""


def generate_sql(question: str) -> str:
    prompt = SQL_PROMPT.replace("<<SCHEMA>>", SCHEMA).replace("<<QUESTION>>", question)
    sql = get_llm().invoke(prompt).content.strip()
    sql = re.sub(r"^```(sql)?|```$", "", sql, flags=re.IGNORECASE | re.MULTILINE).strip()  # enlève les ```
    return sql.rstrip(";").strip()


def validate_sql(sql: str) -> str:
    lowered = sql.strip().lower()
    if not lowered.startswith(("select", "with")):
        raise UnsafeSQLError("Seules les requêtes SELECT sont autorisées")
    if ";" in sql:
        raise UnsafeSQLError("Une seule instruction à la fois")
    if FORBIDDEN.search(sql):
        raise UnsafeSQLError("Mot-clé interdit dans la requête")
    if " limit " not in f" {lowered} ":
        sql = f"{sql} LIMIT 100"
    return sql


def run_sql(question: str) -> dict:
    sql = validate_sql(generate_sql(question))
    with readonly_engine.connect() as conn:            # connexion avec l'utilisateur lecture seule
        rows = [dict(r) for r in conn.execute(text(sql)).mappings().all()]
    return {"sql": sql, "rows": rows}


def readable(value):
    """Decimal('772392.1568627…') -> 772392.16 : un nombre lisible pour le LLM comme pour l'humain."""
    if isinstance(value, (Decimal, float)):
        return round(float(value), 2)
    return value


def answer_with_sql(question: str) -> dict:
    result = run_sql(question)
    rows = [{k: readable(v) for k, v in row.items()} for row in result["rows"][:20]]
    # Un petit LLM se trompe facilement quand il additionne ou compare des nombres.
    # On lui interdit donc tout calcul : il ne fait que citer. Les lignes exactes sont aussi
    # renvoyées à l'interface, qui les affiche dans un tableau (la vérité reste visible).
    summary_prompt = (f"Question : {question}\n"
                      f"Résultat EXACT de la base (JSON, {len(result['rows'])} ligne(s)) : "
                      f"{json.dumps(rows, default=str, ensure_ascii=False)}\n"
                      "Réponds en une ou deux phrases, dans la langue de la question.\n"
                      "Règles : cite les valeurs telles qu'elles apparaissent dans le résultat ; "
                      "ne fais AUCUN calcul (pas de total, pas de moyenne) ; ne renomme pas les catégories.")
    result["answer"] = get_llm().invoke(summary_prompt).content.strip()
    result["rows"] = json.loads(json.dumps(rows, default=str))   # dates, Decimal… -> types JSON simples
    return result