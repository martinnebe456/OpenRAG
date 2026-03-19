#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# AIRAGChat Backend Entrypoint
# 1. Validates critical env vars
# 2. Runs Alembic migrations
# 3. Starts the application (uvicorn or celery, depending on $1)
# -------------------------------------------------------------------

echo "[entrypoint] Starting AIRAGChat backend (mode=${1:-api})..."

# -- 1. Validate required environment --------------------------------
if [ -z "${APP_SECRETS_MASTER_KEY:-}" ]; then
    echo "[entrypoint] ERROR: APP_SECRETS_MASTER_KEY is not set."
    echo '  Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
    exit 1
fi

if [ -z "${DATABASE_URL:-}" ]; then
    echo "[entrypoint] ERROR: DATABASE_URL is not set."
    exit 1
fi

# -- 2. Run database migrations (only for api mode) ------------------
MODE="${1:-api}"

if [ "$MODE" = "api" ]; then
    echo "[entrypoint] Running Alembic migrations..."
    alembic upgrade head
    echo "[entrypoint] Migrations complete."
fi

# -- 3. Start the requested process ---------------------------------
case "$MODE" in
    api)
        echo "[entrypoint] Starting uvicorn..."
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
        ;;
    api-dev)
        echo "[entrypoint] Starting uvicorn (dev/reload)..."
        exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    worker)
        echo "[entrypoint] Starting Celery worker..."
        exec celery -A app.workers.celery_app.celery_app worker \
            -Q ingestion,evals,default -l info
        ;;
    beat)
        echo "[entrypoint] Starting Celery Beat scheduler..."
        exec celery -A app.workers.celery_app.celery_app beat -l info
        ;;
    *)
        echo "[entrypoint] Unknown mode: $MODE"
        echo "  Usage: entrypoint.sh {api|api-dev|worker|beat}"
        exit 1
        ;;
esac
