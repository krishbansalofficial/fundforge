FROM python:3.13-slim AS api
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /bin/uv
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/src ./src
COPY fixtures /app/fixtures
RUN uv sync --frozen --no-dev && useradd --system --uid 10001 --no-create-home fundforge
ENV FUNDFORGE_FIXTURES=/app/fixtures PORT=8000 PATH=/app/backend/.venv/bin:$PATH
USER 10001
# uvicorn trusts X-Forwarded-For only from FORWARDED_ALLOW_IPS (default 127.0.0.1); the prod compose sets the proxy's address.
CMD ["sh", "-c", "exec uvicorn fundforge.api:app --host 0.0.0.0 --port ${PORT}"]

# Nightly dump plus restore-and-verify (deploy/compose.prod.yaml). Built on the server's own image so pg_dump
# always matches the postgres:17 server; the API stage's Python runtime (same Debian trixie base) and venv are copied in.
FROM postgres:17-trixie AS backup
COPY --from=api /usr/local /usr/local
COPY --from=api /app /app
COPY deploy/backup-loop.sh /usr/local/bin/backup-loop
# A new named volume copies this directory's ownership, so the non-root user can write archives.
RUN mkdir /backups && chown 10001 /backups
ENV FUNDFORGE_FIXTURES=/app/fixtures PATH=/app/backend/.venv/bin:/usr/local/bin:$PATH PG_BIN=/usr/lib/postgresql/17/bin
USER 10001
ENTRYPOINT []
CMD ["backup-loop"]
