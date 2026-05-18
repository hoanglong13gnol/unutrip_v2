# Build from repository root: docker build -f backend/rag/Dockerfile backend/rag
FROM python:3.12-slim-bookworm

WORKDIR /svc

ENV PYTHONPATH=/svc \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md ./
COPY app core domain generation llm pipelines providers retrieval services ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY jobs scripts eval data ./ 
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
