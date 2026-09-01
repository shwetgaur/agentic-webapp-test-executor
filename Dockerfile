# Playwright base image includes Chromium and system deps
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HEADLESS=true

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY src ./src
COPY frontend ./frontend
COPY config ./config
COPY schemas ./schemas
COPY tests/samples ./tests/samples

RUN mkdir -p data/reports data/screenshots

EXPOSE 8000

CMD ["sh", "-c", "uvicorn src.backend.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
