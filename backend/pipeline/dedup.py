"""Supprime les quasi-doublons en comparant le sens des textes."""
import numpy as np
import pandas as pd

from backend.app.core.llm import get_embeddings


def remove_near_duplicates(df: pd.DataFrame, threshold: float = 0.97) -> pd.DataFrame:
    vectors = np.array(get_embeddings().embed_documents(df["text"].tolist()))   # 1 ligne = 1 texte
    # On divise chaque vecteur par sa longueur : ensuite, un simple produit = la similarité cosinus.
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    similarity = vectors @ vectors.T          # matrice N x N : similarity[i, j] = ressemblance entre i et j

    keep, removed = [], set()
    for i in range(len(df)):
        if i in removed:
            continue
        keep.append(i)
        # Les textes APRÈS i qui ressemblent trop à i sont marqués comme doublons.
        duplicates = np.where(similarity[i, i + 1:] >= threshold)[0] + i + 1
        removed.update(duplicates.tolist())
    print(f"Dédoublonnage : {len(removed)} quasi-doublons supprimés")
    return df.iloc[keep].reset_index(drop=True)