"""Construit le tableau de nombres (X) que le modèle utilise."""
import numpy as np
import pandas as pd

from backend.app.db.session import engine
from backend.app.models.tender import SECTORS

KEYWORDS = ["application", "data", "logiciel", "système", "web", "digital", "plateforme", "software", "system"]

FEATURE_SQL = """
SELECT f.tender_id, f.reference, f.title, f.language, f.budget_tnd::float AS budget_tnd,
    s.name AS sector, c.name AS country,
    dp.full_date AS publication_date, dd.full_date AS deadline, f.is_relevant
FROM fact_tender f
LEFT JOIN dim_sector  s  ON s.sector_id  = f.sector_id
LEFT JOIN dim_country c  ON c.country_id = f.country_id
LEFT JOIN dim_date    dp ON dp.date_id   = f.publication_date_id
LEFT JOIN dim_date    dd ON dd.date_id   = f.deadline_date_id
"""


def load_tenders() -> pd.DataFrame:
    """Lit toutes les fiches depuis le schéma en étoile (un JOIN par dimension)."""
    return pd.read_sql(FEATURE_SQL, engine)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne de df -> une ligne de nombres. Les colonnes sont TOUJOURS les mêmes, dans le même ordre."""
    X = pd.DataFrame(index=df.index)
    # log1p écrase les très grands budgets : 10 000 et 10 000 000 deviennent 9,2 et 16,1.
    X["budget_log"] = np.log1p(df["budget_tnd"].fillna(0).astype(float))
    delay = pd.to_datetime(df["deadline"]) - pd.to_datetime(df["publication_date"])
    X["days_to_deadline"] = delay.dt.days.fillna(0)
    X["is_english"] = (df["language"] == "en").astype(int)
    X["is_tunisia"] = (df["country"] == "Tunisie").astype(int)
    title = df["title"].fillna("").str.lower()
    for kw in KEYWORDS:                                  # 1 si le mot est dans le titre, sinon 0
        X[f"kw_{kw}"] = title.str.contains(kw, regex=False).astype(int)
    for sector in SECTORS:                               # "one-hot encoding" : une colonne 0/1 par secteur
        X[f"sector_{sector}"] = (df["sector"] == sector).astype(int)
    return X