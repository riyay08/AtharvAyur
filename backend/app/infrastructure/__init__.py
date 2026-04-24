"""Infrastructure layer.

Concrete adapters implementing `app.application.ports.*`. May import SQLAlchemy,
Pydantic, google.genai, httpx, jose, etc. MUST NOT be imported by `app.domain`
or `app.application`.
"""
