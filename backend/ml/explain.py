"""Transforme les valeurs SHAP en phrases compréhensibles."""
import pandas as pd
import shap
from xgboost import XGBClassifier

from backend.ml.train import MODEL_PATH

FEATURE_LABELS = {
    "budget_log": "le budget",
    "days_to_deadline": "le délai pour répondre",
    "is_english": "l'avis est en anglais",
    "is_tunisia": "le pays est la Tunisie",
}


def human_label(feature: str) -> str:
    """'sector_btp' -> 'le secteur btp' ; 'kw_data' -> 'le mot « data » dans le titre'."""
    if feature.startswith("sector_"):
        return f"le secteur {feature.removeprefix('sector_')}"
    if feature.startswith("kw_"):
        return f"le mot « {feature.removeprefix('kw_')} » dans le titre"
    return FEATURE_LABELS.get(feature, feature)


def load_model() -> XGBClassifier:
    model = XGBClassifier()
    model.load_model(MODEL_PATH)
    return model


class ScoreExplainer:
    """Regroupe le modèle et son explicateur SHAP (on les crée une seule fois : c'est coûteux)."""

    def __init__(self, model: XGBClassifier):
        self.model = model
        self.explainer = shap.TreeExplainer(model)     # algorithme SHAP rapide, spécial "arbres"

    def score(self, X: pd.DataFrame) -> list[float]:
        return self.model.predict_proba(X)[:, 1].tolist()

    def explain(self, X_row: pd.DataFrame, top_k: int = 3) -> list[dict]:
        """X_row = un tableau d'UNE ligne. Renvoie les top_k raisons, les plus fortes d'abord."""
        values = self.explainer(X_row).values[0]       # une contribution par feature
        contributions = pd.Series(values, index=X_row.columns)
        top = contributions.abs().sort_values(ascending=False).head(top_k).index
        return [{
            "feature": f,
            "label": human_label(f),
            "value": float(X_row.iloc[0][f]),
            "impact": round(float(contributions[f]), 3),
            "direction": "augmente" if contributions[f] > 0 else "diminue",
        } for f in top]