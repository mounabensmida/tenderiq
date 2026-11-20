import numpy as np
import pandas as pd

from backend.ml.drift import psi
from backend.pipeline.clean import clean_text
from backend.rag.ingest import chunk_text


def test_clean_text():
    assert clean_text("  AVIS   N°1 \n\n\n Budget ") == "AVIS N°1\nBudget"


def test_chunks_se_chevauchent():
    # Les morceaux commencent à 0, 650, 1300 et 1950 (on avance de 800 - 150 = 650) : 4 morceaux.
    chunks = chunk_text("a" * 2000, size=800, overlap=150)
    assert len(chunks) == 4 and all(len(c) <= 800 for c in chunks)


def test_psi_stable_et_derive():
    rng = np.random.default_rng(0)
    ref = pd.Series(rng.normal(12, 1, 2000))
    assert psi(ref, pd.Series(rng.normal(12, 1, 2000))) < 0.1      # même distribution
    assert psi(ref, pd.Series(rng.normal(14, 1, 2000))) > 0.25     # distribution décalée