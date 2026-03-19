FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl wget git \
    && rm -rf /var/lib/apt/lists/*

# ---- dev stage: includes dev dependencies + hot reload -------------
FROM base AS dev
COPY . /app
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .[dev]
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["api-dev"]

# ---- runtime stage: production dependencies only -------------------
FROM base AS runtime
COPY . /app
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e .
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["api"]
