"""Rédaction et envoi d'e-mails (l'envoi n'est appelé qu'APRÈS validation humaine)."""
import re
import smtplib
from email.message import EmailMessage

from pydantic import BaseModel, field_validator
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.llm import get_llm
from backend.app.db.session import readonly_engine
from backend.rag.search import REFERENCE_PATTERN


class EmailDraft(BaseModel):
    to: str
    subject: str
    body: str

    @field_validator("to")
    @classmethod
    def check_email(cls, value: str) -> str:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("adresse e-mail invalide")
        return value


def tender_summary(question: str) -> str:
    """Si la question cite une référence, on récupère la fiche pour nourrir l'e-mail."""
    match = REFERENCE_PATTERN.search(question)
    if not match:
        return ""
    with readonly_engine.connect() as conn:
        row = conn.execute(text("SELECT reference, title, budget_tnd, score, justification "
                                "FROM fact_tender WHERE reference = :r"), {"r": match.group(0)}).mappings().first()
    return str(dict(row)) if row else ""


def draft_email(question: str) -> EmailDraft:
    prompt = ("Rédige un e-mail professionnel court à partir de la demande ci-dessous.\n"
            'Réponds en JSON : {"to": "adresse", "subject": "objet", "body": "texte"}.\n'
            f"Informations sur l'appel d'offres : {tender_summary(question) or 'aucune'}\n"
            f"Demande : {question}")
    response = get_llm(json_mode=True).invoke(prompt)
    return EmailDraft.model_validate_json(response.content)


def send_email(draft: EmailDraft) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = settings.smtp_from, draft.to, draft.subject
    msg.set_content(draft.body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:   # Mailpit en local
        smtp.send_message(msg)