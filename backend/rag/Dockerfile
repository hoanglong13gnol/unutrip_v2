# Build from repository root: docker build -f backend/rag/Dockerfile backend/rag
FROM python:3.12-slim-bookworm

WORKDIR /svc

ENV PYTHONPATH=/svc \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md ./
COPY app core domain generation llm pipelines providers repositories retrieval services ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY jobs scripts eval data ./
COPY tests/fixtures ./tests/fixtures
RUN pip install --no-cache-dir --no-deps -e. \
    && python jobs/build_rag_artifacts.py --from-fixture \
    && chmod +x scripts/docker_entrypoint.sh

EXPOSE 8001

ENTRYPOINT ["scripts/docker_entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
