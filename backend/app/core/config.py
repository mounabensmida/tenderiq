"""Configuration centrale : lit le fichier .env une seule fois."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    # Où trouver le .env, et ignorer les variables qu'on n'a pas déclarées ici.
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # Chaque attribut correspond à une ligne du .env (POSTGRES_HOST -> postgres_host).
    # La valeur après "=" est la valeur par défaut si la ligne est absente.
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "tenderiq"
    postgres_user: str = "tenderiq"
    postgres_password: str = "change_me"
    postgres_readonly_user: str = "tenderiq_ro"
    postgres_readonly_password: str = "change_me_ro"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "tdr_chunks"
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:3b"
    embedding_model: str = "nomic-embed-text"

    mlflow_tracking_uri: str = "http://localhost:5000"

    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    jwt_secret: str = "change_me_long_random_string"
    jwt_expire_minutes: int = 60

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_from: str = "tenderiq@example.local"

    eval_rag_min_score: float = 0.70
    eval_sql_min_accuracy: float = 0.80

    @property
    def database_url(self) -> str:
        # Format SQLAlchemy : dialecte+pilote://utilisateur:motdepasse@hôte:port/base
        return (f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}")

    @property
    def readonly_database_url(self) -> str:
        # Même base, mais avec l'utilisateur qui n'a le droit QUE de lire.
        return (f"postgresql+psycopg://{self.postgres_readonly_user}:{self.postgres_readonly_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}")


# On crée l'objet une seule fois ; les autres fichiers font :
# from backend.app.core.config import settings
settings = Settings()
