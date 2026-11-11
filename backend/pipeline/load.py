"""Écrit une fiche validée dans PostgreSQL (dimensions + fait)."""
from datetime import date

from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.models.tender import TenderExtract


def get_or_create(conn, table: str, id_col: str, name: str) -> int:
    """Renvoie l'id de 'name' dans la dimension ; le crée s'il n'existe pas encore.

    ON CONFLICT ... DO UPDATE ... RETURNING : en une seule requête, on insère OU on récupère l'existant.
    (table et id_col viennent de notre code, jamais de l'utilisateur : pas de risque d'injection.)
    """
    sql = text(f"INSERT INTO {table} (name) VALUES (:name) "
            f"ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING {id_col}")
    return conn.execute(sql, {"name": name}).scalar_one()


def get_date_id(conn, d: date | None) -> int | None:
    if d is None:
        return None
    date_id = int(d.strftime("%Y%m%d"))                   # 2026-03-15 -> 20260315
    conn.execute(text("""INSERT INTO dim_date (date_id, full_date, year, month, day, weekday)
                        VALUES (:id, :d, :y, :m, :day, :wd) ON CONFLICT (date_id) DO NOTHING"""),
                {"id": date_id, "d": d, "y": d.year, "m": d.month, "day": d.day, "wd": d.weekday()})
    return date_id


def save_tender(t: TenderExtract, source: str, url: str, pdf_path: str | None, label: int | None) -> None:
    # engine.begin() ouvre une TRANSACTION : tout est enregistré, ou rien si une erreur survient.
    with engine.begin() as conn:
        params = {
            "reference": t.reference, "title": t.title, "description": t.description,
            "language": t.language, "budget": t.budget_tnd, "url": url, "pdf": pdf_path,
            "label": None if label is None else bool(label),
            "buyer": get_or_create(conn, "dim_buyer", "buyer_id", t.buyer),
            "sector": get_or_create(conn, "dim_sector", "sector_id", t.sector),
            "country": get_or_create(conn, "dim_country", "country_id", t.country),
            "source": get_or_create(conn, "dim_source", "source_id", source),
            "pub": get_date_id(conn, t.publication_date),
            "deadline": get_date_id(conn, t.deadline),
        }
        # Les ":nom" sont des PARAMÈTRES : SQLAlchemy les échappe, ce qui empêche l'injection SQL.
        conn.execute(text("""
            INSERT INTO fact_tender (reference, title, description, language, budget_tnd, buyer_id, sector_id,
                                    country_id, source_id, publication_date_id, deadline_date_id, url,
                                    pdf_path, is_relevant)
            VALUES (:reference, :title, :description, :language, :budget, :buyer, :sector, :country, :source,
                    :pub, :deadline, :url, :pdf, :label)
            ON CONFLICT (reference) DO NOTHING
        """), params)