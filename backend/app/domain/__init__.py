"""Domain layer.

Pure Python only. MUST NOT import from:
  - SQLAlchemy / databases
  - FastAPI / Starlette / Pydantic
  - google.genai / httpx / APScheduler / any outbound SDK
  - Any module under `app.infrastructure`, `app.interfaces`, `app.application`

Allowed imports: stdlib and other modules under `app.domain`.
"""
