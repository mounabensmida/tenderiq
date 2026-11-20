"""Serveur MCP : expose les outils de TenderIQ à n'importe quel assistant compatible.

    python -m backend.mcp_server.server      # dialogue par l'entrée/sortie standard (stdio)
"""
from mcp.server.mcpserver import MCPServer
from sqlalchemy import text

from backend.agent.sql_tool import UnsafeSQLError, answer_with_sql
from backend.app.db.session import readonly_engine
from backend.rag.answer import answer_question

mcp = MCPServer("TenderIQ")


# Le décorateur @mcp.tool() publie la fonction. Sa docstring et ses types deviennent la "notice"
# que l'assistant lit pour savoir quand et comment l'appeler : soigne-les !
@mcp.tool()
def search_tender_documents(question: str) -> dict:
    """Répond à une question sur le contenu des termes de référence (TDR) des appels d'offres,
    avec les citations (référence du document et numéro de page)."""
    return answer_question(question)


@mcp.tool()
def tender_statistics(question: str) -> dict:
    """Répond à une question statistique (comptage, moyenne, classement) sur les appels d'offres,
    en générant une requête SQL en lecture seule."""
    try:
        return answer_with_sql(question)
    except UnsafeSQLError as error:
        return {"error": str(error)}


@mcp.tool()
def top_tenders(limit: int = 5) -> list[dict]:
    """Renvoie les appels d'offres ayant le meilleur score de pertinence."""
    with readonly_engine.connect() as conn:
        rows = conn.execute(text("SELECT reference, title, round(score::numeric, 2) AS score, justification "
                                "FROM fact_tender WHERE score IS NOT NULL ORDER BY score DESC LIMIT :n"),
                            {"n": min(limit, 20)}).mappings().all()
    return [dict(r, score=float(r["score"])) for r in rows]


if __name__ == "__main__":
    mcp.run()        # transport stdio par défaut