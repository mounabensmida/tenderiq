"""Lance tout le pipeline.

    python -m backend.pipeline.run --limit 30            # avec le LLM (lent mais c'est le vrai pipeline)
    python -m backend.pipeline.run --no-llm              # sans LLM : utilise la fiche 'truth' du générateur
"""
import argparse
import math
import time

from backend.app.core.config import ROOT
from backend.app.models.tender import TenderExtract
from backend.pipeline.clean import load_and_clean
from backend.pipeline.dedup import remove_near_duplicates
from backend.pipeline.extract import extract_tender
from backend.pipeline.load import save_tender


def clean_value(v):
    """pandas met NaN (nombre 'vide') là où une colonne manque : on le remplace par None."""
    return None if isinstance(v, float) and math.isnan(v) else v


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(ROOT / "data" / "samples" / "tenders.jsonl"))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--no-dedup", action="store_true")
    args = parser.parse_args()

    df = load_and_clean(args.input)
    print(f"{len(df)} avis après nettoyage")
    if not args.no_dedup:
        df = remove_near_duplicates(df)
    if args.limit:
        df = df.head(args.limit)

    ok, failed, start = 0, 0, time.time()
    for _, row in df.iterrows():                      # une itération = un avis
        if args.no_llm:
            tender = TenderExtract(**row["truth"])     # ** "déplie" le dictionnaire en arguments
        else:
            tender = extract_tender(row["text"])
        if tender is None:
            failed += 1
            continue
        save_tender(tender, row["source"], row["url"], clean_value(row.get("pdf_path")),
                    clean_value(row.get("label")))
        ok += 1
        print(f"  ✓ {tender.reference} | {tender.sector} | {tender.budget_tnd}")
    print(f"Terminé : {ok} enregistrés, {failed} échecs, {time.time() - start:.0f} s")


if __name__ == "__main__":
    main()