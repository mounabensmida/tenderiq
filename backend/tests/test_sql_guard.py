import pytest

from backend.agent.sql_tool import UnsafeSQLError, validate_sql


@pytest.mark.parametrize("sql", [                    # le même test est lancé pour chaque requête
    "DROP TABLE fact_tender",
    "DELETE FROM fact_tender",
    "SELECT * FROM fact_tender; DROP TABLE fact_tender",
    "WITH x AS (DELETE FROM fact_tender RETURNING *) SELECT * FROM x",
    "SELECT pg_sleep(60)",
    "UPDATE fact_tender SET score = 1",
])
def test_requetes_dangereuses_refusees(sql):
    with pytest.raises(UnsafeSQLError):
        validate_sql(sql)


def test_limit_ajoute_automatiquement():
    assert validate_sql("SELECT name FROM dim_sector").endswith("LIMIT 100")


def test_limit_existant_conserve():
    assert validate_sql("SELECT name FROM dim_sector LIMIT 5") == "SELECT name FROM dim_sector LIMIT 5"