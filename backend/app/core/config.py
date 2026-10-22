from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "BugForge AI"
    environment: str = "development"
    database_url: str = "sqlite:///./bugforge.db"
    session_secret: str = "dev-only-change-me-session-secret-32chars!!"
    token_encryption_key: str = ""  # Fernet key; derived from session_secret if empty
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8000/api/v1/github/callback"
    llm_provider: str = "openai-compatible"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    max_source_bytes: int = 200_000
    max_files: int = 20
    max_file_bytes: int = 100_000

    @property
    def google_configured(self) -> bool: return bool(self.google_client_id and self.google_client_secret)
    @property
    def github_configured(self) -> bool: return bool(self.github_client_id and self.github_client_secret)
    @property
    def llm_configured(self) -> bool: return bool(self.llm_api_key)
    @property
    def cors_list(self): return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings: return Settings()
