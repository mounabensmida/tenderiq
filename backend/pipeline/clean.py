"""Nettoyage du texte brut."""
import re
import unicodedata

import pandas as pd


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)        # unifie les caractères bizarres (espaces insécables…)
    text = re.sub(r"[ \t]+", " ", text)                # plusieurs espaces -> un seul
    text = re.sub(r" *\n *", "\n", text)               # pas d'espace autour des retours à la ligne
    text = re.sub(r"\n{2,}", "\n", text)               # lignes vides multiples -> une seule
    return text.strip()                                 # enlève les espaces au début et à la fin


def load_and_clean(path) -> pd.DataFrame:
    df = pd.read_json(path, lines=True)                 # lines=True car c'est du JSONL
    df["text"] = df["raw_text"].astype(str).map(clean_text)   # .map applique la fonction à chaque ligne
    df = df[df["text"].str.len() > 50]                  # on jette les textes trop courts (pages vides)
    df = df.drop_duplicates(subset="text")              # doublons EXACTS
    return df.reset_index(drop=True)                    # renumérote les lignes 0, 1, 2…