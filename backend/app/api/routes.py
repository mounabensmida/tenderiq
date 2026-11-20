"""Les 'guichets' de l'API."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from langgraph.types import Command
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field
from sqlalchemy import text

from backend.agent.graph import graph
from backend.app.core.observability import get_callbacks
from backend.app.core.security import authenticate, create_token, get_current_user, require_role
from backend.app.db.session import readonly_engine

router = APIRouter()

# Métriques métier, lues par Prometheus à l'étape 18.
QUESTIONS = Counter("tenderiq_questions_total", "Questions posées à l'agent", ["route"])
ASK_SECONDS = Histogram("tenderiq_ask_seconds", "Durée de traitement d'une question (s)")


class AskRequest(BaseModel):
    # Les contraintes protègent aussi l'API : pas de question vide ni de roman de 50 pages.
    question: str = Field(min_length=3, max_length=1000)


class ApproveRequest(BaseModel):
    thread_id: str
    decision: Literal["approve", "reject"]


@router.post("/auth/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(form.username, form.password)
    if not user:
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": create_token(form.username, user["role"]), "token_type": "bearer"}


@router.get("/tenders")
def list_tenders(min_score: float = 0.0, limit: int = Query(20, ge=1, le=100),
            user: dict = Depends(get_current_user)):
    with readonly_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT f.reference, f.title, s.name AS sector, c.name AS country, f.budget_tnd,
                d.full_date AS deadline, f.score, f.score_reasons, f.justification
            FROM fact_tender f
            LEFT JOIN dim_sector s USING (sector_id)
            LEFT JOIN dim_country c USING (country_id)
            LEFT JOIN dim_date d ON d.date_id = f.deadline_date_id
            WHERE COALESCE(f.score, 0) >= :min_score
            ORDER BY f.score DESC NULLS LAST
            LIMIT :limit"""), {"min_score": min_score, "limit": limit}).mappings().all()
    return [dict(r) for r in rows]


@router.post("/ask")
def ask(req: AskRequest, user: dict = Depends(get_current_user)):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "callbacks": get_callbacks()}
    with ASK_SECONDS.time():                         # mesure la durée du bloc
        result = graph.invoke({"question": req.question}, config)
    QUESTIONS.labels(route=result.get("route", "inconnue")).inc()
    if "__interrupt__" in result:                    # l'agent attend une validation humaine
        return {"status": "pending_approval", "thread_id": thread_id, "route": "email",
                "draft": result["__interrupt__"][0].value["draft"]}
    return {"status": "done", "route": result.get("route"), "answer": result.get("answer"),
            "sources": result.get("sources", []), "sql": result.get("sql")}


@router.post("/approve")
def approve(req: ApproveRequest, user: dict = Depends(require_role("admin"))):   # RBAC : admin seulement
    config = {"configurable": {"thread_id": req.thread_id}, "callbacks": get_callbacks()}
    if not graph.get_state(config).next:             # aucun graphe en pause pour ce thread_id
        raise HTTPException(404, "Aucune action en attente pour cet identifiant")
    result = graph.invoke(Command(resume=req.decision), config)
    return {"status": "done", "approved": result.get("approved", False), "answer": result.get("answer"),
            "validated_by": user["username"]}