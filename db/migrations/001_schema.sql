-- ===== Dimensions : les "fiches descriptives" =====
CREATE TABLE dim_buyer (
    buyer_id SERIAL PRIMARY KEY, -- SERIAL = numéro auto-incrémenté (1, 2, 3…)
    name TEXT UNIQUE NOT NULL -- UNIQUE : pas deux fois le même acheteur
);

CREATE TABLE dim_sector (
    sector_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL -- informatique, btp, sante…
);

CREATE TABLE dim_country (
    country_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE dim_source (
    source_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL -- le site d'où vient l'avis
);

-- La dimension date a une clé "intelligente" : 20260315 pour le 15 mars 2026.
CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INT, month INT, day INT,
    weekday INT  -- 0 = lundi … 6 = dimanche
);

-- ===== Table de faits : une ligne = un appel d'offres =====
CREATE TABLE fact_tender (
    tender_id            SERIAL PRIMARY KEY,
    reference            TEXT UNIQUE NOT NULL, -- ex. AO-2026-0001 ; UNIQUE = anti-doublon
    title                TEXT NOT NULL,
    description          TEXT,
    language             TEXT,
    budget_tnd           NUMERIC,
    buyer_id             INT REFERENCES dim_buyer(buyer_id), -- clé étrangère vers une dimension
    sector_id            INT REFERENCES dim_sector(sector_id),
    country_id           INT REFERENCES dim_country(country_id),
    source_id            INT REFERENCES dim_source(source_id),
    publication_date_id  INT REFERENCES dim_date(date_id),
    deadline_date_id     INT REFERENCES dim_date(date_id),
    url                  TEXT,
    pdf_path             TEXT,
    is_relevant          BOOLEAN,       -- décision passée de l'entreprise (sert à entraîner le modèle)
    score                REAL,          -- probabilité calculée par XGBoost (0 à 1)
    score_reasons        JSONB,                -- les raisons SHAP, stockées en JSON
    justification        TEXT,          -- l'explication rédigée par le LLM
    created_at           TIMESTAMPTZ DEFAULT now()
);

-- ===== Utilisateur en LECTURE SEULE pour le Text-to-SQL =====
-- Même si le LLM génère un "DELETE", Postgres refusera : c'est la ceinture de sécurité.
CREATE ROLE tenderiq_ro LOGIN PASSWORD 'change_me_ro';
GRANT CONNECT ON DATABASE tenderiq TO tenderiq_ro;
GRANT USAGE ON SCHEMA public TO tenderiq_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO tenderiq_ro;
ALTER ROLE tenderiq_ro SET default_transaction_read_only = on;
ALTER ROLE tenderiq_ro SET statement_timeout = '5s'; -- une requête trop longue est coupée
