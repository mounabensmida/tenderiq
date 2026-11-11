"""Connexions à PostgreSQL."""
from sqlalchemy import create_engine
from backend.app.core.config import settings
# Un "engine" gère un groupe de connexions réutilisables (un pool).
# pool_pre_ping vérifie qu'une connexion est encore vivante avant de s'en servir.
engine = create_engine(settings.database_url, pool_pre_ping=True) # lecture + écriture
readonly_engine = create_engine(settings.readonly_database_url, pool_pre_ping=True) # lecture seule
