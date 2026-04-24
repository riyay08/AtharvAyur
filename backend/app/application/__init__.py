"""Application layer.

Use cases orchestrate domain entities/services through ports (interfaces). MUST NOT
import SQLAlchemy, FastAPI, Pydantic, httpx, or any SDK. Concrete adapters for the
ports live under `app.infrastructure`.
"""
