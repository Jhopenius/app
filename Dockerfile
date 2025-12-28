FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/
COPY src /app/src
COPY README.md /app/README.md
COPY entrypoint.sh /app/entrypoint.sh
COPY .streamlit /app/.streamlit

RUN uv pip install --system .

ENV PYTHONPATH=/app/src

RUN mkdir -p /app/backups \
    && chmod +x /app/entrypoint.sh

EXPOSE 8501

CMD ["/app/entrypoint.sh"]
