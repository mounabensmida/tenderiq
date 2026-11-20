from datetime import date

import pytest
from pydantic import ValidationError

from backend.app.models.tender import TenderExtract

BASE = {"reference": "AO-2026-0001", "title": "Plateforme data", "buyer": "STEG"}


def test_alias_de_secteur():
    assert TenderExtract(**BASE, sector="IT").sector == "informatique"


def test_secteur_inconnu_devient_autre():
    assert TenderExtract(**BASE, sector="pêche").sector == "autre"


def test_budget_negatif_refuse():
    with pytest.raises(ValidationError):
        TenderExtract(**BASE, budget_tnd=-10)


def test_date_texte_convertie():
    assert TenderExtract(**BASE, publication_date="2026-03-15").publication_date == date(2026, 3, 15)


def test_langue_normalisee():
    assert TenderExtract(**BASE, language="English").language == "en"