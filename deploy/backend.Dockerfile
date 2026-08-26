ARG PYTHON_IMAGE=python:3.13.2-slim-bookworm@sha256:6b3223eb4d93718828223966ad316909c39813dee3ee9395204940500792b740
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.11.6@sha256:b1e699368d24c57cda93c338a57a8c5a119009ba809305cc8e86986d4a006754

FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY services/backend ./services/backend
RUN uv sync --frozen --no-dev --no-editable

FROM ${PYTHON_IMAGE} AS runtime
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 echoatlas \
    && useradd --uid 10001 --gid echoatlas --no-create-home --shell /usr/sbin/nologin echoatlas \
    && mkdir -p /app/data \
    && chown -R echoatlas:echoatlas /app
WORKDIR /app
COPY --from=builder --chown=echoatlas:echoatlas /app/.venv /app/.venv
COPY --chown=echoatlas:echoatlas schemas /app/schemas
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read()"]
CMD ["uvicorn", "echoatlas.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
