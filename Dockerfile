FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY gemini_sync_bridge /app/gemini_sync_bridge
COPY connectors /app/connectors
COPY schemas /app/schemas
COPY scripts /app/scripts

RUN pip install --no-cache-dir .

EXPOSE 8080

CMD ["gemini-sync-bridge", "serve", "--host", "0.0.0.0", "--port", "8080"]
