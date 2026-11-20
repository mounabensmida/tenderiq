"""Connexions à PostgreSQL."""
from sqlalchemy import create_engine

from backend.app.core.config import settings

# Un "engine" gère un groupe de connexions réutilisables (un pool).
# pool_pre_ping vérifie qu'une connexion est encore vivante avant de s'en servir.
# connect_timeout=3 : si Postgres ne répond pas en 3 s (Docker arrêté), on abandonne
# avec une erreur claire au lieu d'attendre longtemps.
CONNECT_ARGS = {"connect_timeout": 3}

engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=CONNECT_ARGS)  # lecture + écriture
readonly_engine = create_engine(settings.readonly_database_url, pool_pre_ping=True,
                                connect_args=CONNECT_ARGS)                                   # lecture seule
