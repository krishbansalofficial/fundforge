FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
COPY fixtures /app/fixtures
RUN uv sync --frozen --no-dev
ENV FUNDFORGE_FIXTURES=/app/fixtures PORT=8000
CMD ["sh", "-c", "uv run --no-sync uvicorn fundforge.api:app --host 0.0.0.0 --port ${PORT}"]
