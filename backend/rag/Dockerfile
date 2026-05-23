# syntax=docker/dockerfile:1
# Build context: backend/rag (see root docker-compose.yml)
FROM python:3.12-slim-bookworm

WORKDIR /svc

ENV PYTHONPATH=/svc \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md ./
COPY app core domain generation llm pipelines providers repositories retrieval services ./

RUN pip install --no-cache-dir --upgrade pip \
    && apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir .

COPY jobs ./jobs
COPY scripts ./scripts
COPY eval ./eval
COPY data ./data
COPY tests/fixtures/rag_corpus_sample.jsonl tests/fixtures/places_app_sample.json ./tests/fixtures/

RUN test -d core \
    && test -f core/__init__.py \
    && python -c "import core.config; print('core import ok')" \
    && test -f scripts/docker_entrypoint.sh \
    && test -f tests/fixtures/rag_corpus_sample.jsonl \
    && sed -i 's/\r$//' scripts/*.sh \
    && chmod +x scripts/docker_entrypoint.sh \
    && python jobs/build_rag_artifacts.py --from-fixture \
    && test -f data/indexes/bm25_index.pkl

EXPOSE 8001

ENTRYPOINT ["/bin/sh", "scripts/docker_entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
