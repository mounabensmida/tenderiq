"""Compare un nouveau lot d'appels d'offres aux données d'entraînement.

    python -m backend.ml.drift --input data/samples/tenders.jsonl          # attendu : pas de dérive
    python -m backend.ml.drift --input data/samples/tenders_drift.jsonl    # attendu : dérive
    python -m backend.ml.drift --input data/samples/tenders_drift.jsonl --retrain
"""
import argparse
import json
import sys

import mlflow
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.ml.features import build_features
from backend.ml.train import REFERENCE_PATH, train

PSI_ALERT = 0.25


def psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    reference, current = reference.astype(float), current.astype(float)
    if reference.nunique() <= 10:
        # Peu de valeurs différentes (0/1…) : chaque valeur est une case.
        cats = sorted(set(reference.unique()) | set(current.unique()))
        ref_pct = reference.value_counts(normalize=True).reindex(cats, fill_value=0).values
        cur_pct = current.value_counts(normalize=True).reindex(cats, fill_value=0).values
    else:
        # Valeurs continues : 10 tranches qui contiennent chacune 10 % des données de référence.
        edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
        edges[0], edges[-1] = -np.inf, np.inf            # la 1re et la dernière case sont ouvertes
        ref_pct = pd.cut(reference, edges).value_counts(normalize=True, sort=False).values
        cur_pct = pd.cut(current, edges).value_counts(normalize=True, sort=False).values
    ref_pct, cur_pct = np.clip(ref_pct, 1e-6, None), np.clip(cur_pct, 1e-6, None)   # évite log(0)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def batch_features(path: str) -> pd.DataFrame:
    """Lit un lot JSONL et construit les mêmes features qu'à l'entraînement."""
    raw = pd.read_json(path, lines=True)
    fiches = pd.json_normalize(raw["truth"])              # le dictionnaire 'truth' devient des colonnes
    return build_features(fiches)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--retrain", action="store_true")
    args = parser.parse_args()

    reference = pd.read_csv(REFERENCE_PATH)
    current = batch_features(args.input)[reference.columns]   # mêmes colonnes, même ordre
    report = {col: round(psi(reference[col], current[col]), 4) for col in reference.columns}
    drifted = {c: v for c, v in report.items() if v > PSI_ALERT}

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("tenderiq-drift")
    with mlflow.start_run():
        mlflow.log_metrics({f"psi_{c}": v for c, v in report.items()})
        mlflow.log_metric("n_drifted_features", len(drifted))
        mlflow.log_dict(report, "psi_report.json")

    print(json.dumps(dict(sorted(report.items(), key=lambda kv: -kv[1])[:8]), indent=2))
    if not drifted:
        print("✓ Pas de dérive")
        return
    print(f"⚠ Dérive détectée sur : {', '.join(drifted)}")
    if args.retrain:
        print("Réentraînement… (charge d'abord le nouveau lot avec : python -m backend.pipeline.run "
                f"--input {args.input} --no-llm)")
        train()
    else:
        sys.exit(1)   # code de sortie 1 = "problème" : une CI ou une tâche planifiée peut réagir


if __name__ == "__main__":
    main()