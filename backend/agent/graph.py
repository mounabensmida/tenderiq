"""L'agent TenderIQ : un routeur et trois chemins, dont un avec validation humaine."""
import json
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from backend.agent.email_tool import EmailDraft, draft_email, send_email
from backend.agent.sql_tool import UnsafeSQLError, answer_with_sql
from backend.app.core.llm import get_llm
from backend.rag.answer import answer_question


class AgentState(TypedDict, total=False):
    """Le 'sac à dos' qui passe de nœud en nœud. total=False : aucune clé n'est obligatoire."""
    question: str
    route: str
    answer: str
    sources: list
    sql: str
    email_draft: dict
    approved: bool


ROUTER_PROMPT = """Classe la question dans UNE catégorie et réponds en JSON {"route": "..."}.
- "documents" : une question sur le CONTENU d'un appel d'offres ou de ses termes de référence
    (exigences, certification, caution, délais, critères…).
- "chiffres" : une question de COMPTAGE, de moyenne, de classement ou de statistiques sur les appels d'offres.
- "email" : une demande d'ENVOYER ou de rédiger un e-mail.
Exemples :
"Quelle caution pour AO-2026-0002 ?" -> {"route": "documents"}
"Combien d'offres en BTP en 2026 ?" -> {"route": "chiffres"}
"How many tenders in Morocco?" -> {"route": "chiffres"}
"Envoie un résumé de AO-2026-0001 à ali@exemple.tn" -> {"route": "email"}
Question : <<QUESTION>>"""


def router_node(state: AgentState) -> dict:
    response = get_llm(json_mode=True).invoke(ROUTER_PROMPT.replace("<<QUESTION>>", state["question"]))
    try:
        route = json.loads(response.content).get("route", "documents")
    except json.JSONDecodeError:
        route = "documents"
    if route not in ("documents", "chiffres", "email"):
        route = "documents"                                  # valeur sûre par défaut
    return {"route": route}                                  # on ne renvoie QUE ce qui change


def rag_node(state: AgentState) -> dict:
    result = answer_question(state["question"])
    return {"answer": result["answer"], "sources": result["sources"]}


def sql_node(state: AgentState) -> dict:
    try:
        result = answer_with_sql(state["question"])
        return {"answer": result["answer"], "sql": result["sql"]}
    except UnsafeSQLError as error:
        return {"answer": f"Requête refusée par le garde-fou : {error}"}
    except Exception as error:                               # SQL invalide généré par le LLM, etc.
        return {"answer": f"Je n'ai pas réussi à calculer la réponse ({type(error).__name__})."}


def draft_email_node(state: AgentState) -> dict:
    try:
        return {"email_draft": draft_email(state["question"]).model_dump()}
    except Exception:
        return {"email_draft": {}, "answer": "Impossible de rédiger l'e-mail : précise l'adresse du destinataire."}


def human_approval_node(state: AgentState) -> dict:
    draft = state.get("email_draft") or {}
    if not draft:
        return {}
    # ⏸ Le graphe s'arrête ici. La valeur passée à interrupt() est montrée à l'humain.
    decision = interrupt({"type": "approval_required", "draft": draft})
    # ▶ On arrive ici seulement à la reprise, avec decision = "approve" ou "reject".
    if decision == "approve":
        send_email(EmailDraft(**draft))
        return {"approved": True, "answer": f"E-mail envoyé à {draft['to']}."}
    return {"approved": False, "answer": "Envoi annulé : rien n'a été envoyé."}


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", router_node)
    g.add_node("rag", rag_node)
    g.add_node("sql", sql_node)
    g.add_node("draft_email", draft_email_node)
    g.add_node("human_approval", human_approval_node)

    g.add_edge(START, "router")
    # L'aiguillage : la fonction lit state["route"] et le dictionnaire dit vers quel nœud aller.
    g.add_conditional_edges("router", lambda s: s["route"],
                            {"documents": "rag", "chiffres": "sql", "email": "draft_email"})
    g.add_edge("rag", END)
    g.add_edge("sql", END)
    g.add_edge("draft_email", "human_approval")
    g.add_edge("human_approval", END)
    # Le checkpointer garde l'état de chaque conversation (thread_id) : indispensable pour interrupt().
    # InMemorySaver = en mémoire (perdu au redémarrage). En production : un checkpointer PostgreSQL.
    return g.compile(checkpointer=InMemorySaver())


graph = build_graph()