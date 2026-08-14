FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/database.db \
    DATABASE_SEED_PATH=/app/database.db

WORKDIR /app

COPY requirements-cloud.txt /app/requirements-cloud.txt
RUN pip install --no-cache-dir -r /app/requirements-cloud.txt

COPY api /app/api
COPY modulos /app/modulos

RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
