# HolisticAI Health API — run on EC2 / App Runner / ECS
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini alembic.ini
COPY alembic ./alembic
COPY app ./app

ENV PYTHONPATH=/app

EXPOSE 8000

# Migrations then API (DATABASE_URL must point at Postgres, e.g. compose service `db`)
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
