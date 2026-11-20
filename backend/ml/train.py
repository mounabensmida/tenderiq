"""Entraîne le modèle de score et enregistre tout dans MLflow.

    python -m backend.ml.train
"""
import matplotlib

matplotlib.use("Agg")                     # dessine dans des fichiers, sans ouvrir de fenêtre
# "noqa: E402" dit au linter : "oui, je sais que ces imports ne sont pas tout en haut, c'est voulu".
import matplotlib.pyplot as plt  # noqa: E402
import mlflow  # noqa: E402
import shap  # noqa: E402
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from xgboost import XGBClassifier  # noqa: E402

from backend.app.core.config import ROOT, settings  # noqa: E402
from backend.ml.features import build_features, load_tenders  # noqa: E402

ARTIFACTS = ROOT / "backend" / "ml" / "artifacts"
MODEL_PATH = ARTIFACTS / "model.json"
REFERENCE_PATH = ARTIFACTS / "reference_features.csv"   # "photo" des données d'entraînement (pour la dérive)


def train(n_estimators: int = 200, max_depth: int = 4, learning_rate: float = 0.1) -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df = load_tenders()
    df = df[df["is_relevant"].notna()]                  # on n'apprend que sur les lignes étiquetées
    X, y = build_features(df), df["is_relevant"].astype(int)

    # 80 % pour apprendre, 20 % pour vérifier sur des données que le modèle n'a JAMAIS vues.
    # stratify=y garde la même proportion de "pertinents" dans les deux parties.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("tenderiq-scoring")
    with mlflow.start_run():                             # tout ce qui suit est noté dans un "run"
        params = {"n_estimators": n_estimators, "max_depth": max_depth, "learning_rate": learning_rate}
        model = XGBClassifier(**params, eval_metric="logloss")
        model.fit(X_train, y_train)

        proba = model.predict_proba(X_test)[:, 1]        # probabilité d'être pertinent (colonne 1)
        pred = (proba >= 0.5).astype(int)
        metrics = {
            "auc": roc_auc_score(y_test, proba),         # 0,5 = hasard ; 1 = parfait
            "f1": f1_score(y_test, pred),                # équilibre entre précision et rappel
            "accuracy": accuracy_score(y_test, pred),
        }
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)

        model.save_model(MODEL_PATH)                      # le modèle, au format JSON d'XGBoost
        X_train.to_csv(REFERENCE_PATH, index=False)
        mlflow.log_artifact(str(MODEL_PATH))
        mlflow.log_artifact(str(REFERENCE_PATH))

        # Graphique SHAP global : quelles features comptent le plus, et dans quel sens.
        shap_values = shap.TreeExplainer(model)(X_test)
        shap.plots.beeswarm(shap_values, show=False)
        plot_path = ARTIFACTS / "shap_summary.png"
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()
        mlflow.log_artifact(str(plot_path))

    print("Métriques :", {k: round(v, 3) for k, v in metrics.items()})
    return metrics


if __name__ == "__main__":
    train()