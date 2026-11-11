"""La 'fiche' d'un appel d'offres, telle qu'on veut la stocker."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SECTORS = ["informatique", "telecom", "etudes", "btp", "sante", "energie", "autre"]


class TenderExtract(BaseModel):
    reference: str = Field(min_length=3)            # obligatoire, au moins 3 caractères
    title: str
    buyer: str
    sector: str = "autre"
    country: str = "Tunisie"
    budget_tnd: float | None = Field(default=None, ge=0)   # ge=0 : jamais négatif ; None si inconnu
    publication_date: date | None = None             # Pydantic convertit "2026-03-15" en vraie date
    deadline: date | None = None
    language: Literal["fr", "en", "ar"] = "fr"       # Literal : seulement ces 3 valeurs
    description: str = ""

    # Un validateur nettoie une valeur AVANT le contrôle de type ("before").
    @field_validator("sector", mode="before")
    @classmethod
    def normalize_sector(cls, value):
        value = str(value or "").lower().strip()
        aliases = {"it": "informatique", "ict": "informatique", "construction": "btp",
                    "health": "sante", "santé": "sante", "energy": "energie", "énergie": "energie",
                    "études": "etudes", "study": "etudes", "telecommunications": "telecom"}
        value = aliases.get(value, value)
        return value if value in SECTORS else "autre"

    @field_validator("language", mode="before")
    @classmethod
    def normalize_language(cls, value):
        value = str(value or "fr").lower()[:2]       # "French" -> "fr", "English" -> "en"
        return value if value in ("fr", "en", "ar") else "fr"