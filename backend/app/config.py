from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always load `backend/.env` regardless of process cwd (uvicorn started from repo root vs backend/).
_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg2://holistica:holistica@127.0.0.1:5432/holistica_health"

    # Which provider implements the LLMGateway port. Supported: "gemini", "groq".
    llm_provider: str = "gemini"

    gemini_api_key: str | None = None
    # Model must support Grounding with Google Search — see https://ai.google.dev/gemini-api/docs/google-search
    gemini_model: str = "gemini-flash-latest"
    gemini_embedding_model: str = "gemini-embedding-001"

    # Groq — https://console.groq.com/docs/models
    # Free tier; no built-in web search or embeddings (semantic history degrades gracefully).
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    immediate_history_limit: int = 3
    semantic_history_limit: int = 5

    jwt_secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"

    # OpenWeatherMap Current Weather API (free tier): https://openweathermap.org/api
    openweather_api_key: str | None = None

    # Comma-separated origins for the Vite dev server / production frontend
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Google Identity Services — required for Google sign-in.
    # Leave blank to hide the "Sign in with Google" button.
    google_client_id: str | None = None

    # WebAuthn relying-party identifiers. `rp_id` must be the browser's
    # registrable domain (usually the apex domain without scheme/port); in
    # local dev the browser treats "localhost" as special-cased.
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "AtharvAyur"
    webauthn_origin: str = "http://localhost:5173"

    # When true, the `/auth/phone/request-otp` response includes the OTP
    # itself (dev-only convenience so you don't need an SMS provider).
    auth_expose_dev_otp: bool = True


settings = Settings()
