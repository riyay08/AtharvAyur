from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg2://holistica:holistica@localhost:5432/holistica_health"
    gemini_api_key: str | None = None
    # Model must support Grounding with Google Search — see https://ai.google.dev/gemini-api/docs/google-search
    gemini_model: str = "gemini-2.5-flash"

    # Comma-separated origins for the Vite dev server / production frontend
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
