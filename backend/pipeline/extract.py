"""Transforme un texte brut en fiche TenderExtract grâce au LLM."""
from pydantic import ValidationError

from backend.app.core.llm import get_llm
from backend.app.models.tender import TenderExtract

# On utilise <<TEXTE>> comme emplacement (et pas {texte}) car le prompt contient des accolades JSON.
PROMPT = """Tu extrais les informations d'un avis d'appel d'offres.
Réponds UNIQUEMENT avec un objet JSON qui a exactement ces clés :
{"reference": str, "title": str, "buyer": str,
"sector": "informatique|telecom|etudes|btp|sante|energie|autre",
"country": str, "budget_tnd": nombre ou null,
"publication_date": "AAAA-MM-JJ" ou null, "deadline": "AAAA-MM-JJ" ou null,
"language": "fr|en|ar", "description": "une phrase qui résume l'objet"}
Règles : le budget est un nombre sans espace ni devise (268 000 TND -> 268000).
N'invente rien : si une information est absente, mets null.

Avis :
---
<<TEXTE>>
---"""


def extract_tender(raw_text: str, retries: int = 2) -> TenderExtract | None:
    llm = get_llm(json_mode=True)
    prompt = PROMPT.replace("<<TEXTE>>", raw_text)
    for attempt in range(retries + 1):
        response = llm.invoke(prompt)                     # envoie le prompt, reçoit un message
        try:
            # model_validate_json lit le JSON ET vérifie tous les types en une fois.
            return TenderExtract.model_validate_json(response.content)
        except ValidationError as error:
            print(f"  essai {attempt + 1} refusé par Pydantic : {error.errors()[0]['msg']}")
    return None                                           # on préfère "rien" à "faux"