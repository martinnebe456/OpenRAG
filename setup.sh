#!/usr/bin/env bash
# =============================================================================
# OpenRAG — One-shot dev setup & launch
# Usage:  ./setup.sh [--no-observability] [--clean]
#
#   --no-observability   Skip Grafana / Jaeger / Prometheus / Loki
#   --clean              Stop containers and wipe all volumes before starting
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$REPO_ROOT/infra/compose/compose.yaml"
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

OBSERVABILITY=true
CLEAN=false

# ── Parse flags ──────────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --no-observability) OBSERVABILITY=false ;;
    --clean)            CLEAN=true ;;
    -h|--help)
      echo "Usage: ./setup.sh [--no-observability] [--clean]"
      exit 0
      ;;
  esac
done

# ── Colour helpers ────────────────────────────────────────────────────────────
info()  { printf "\033[1;36m[INFO]\033[0m  %s\n" "$*"; }
ok()    { printf "\033[1;32m[ OK ]\033[0m  %s\n" "$*"; }
warn()  { printf "\033[1;33m[WARN]\033[0m  %s\n" "$*"; }
err()   { printf "\033[1;31m[ERR ]\033[0m  %s\n" "$*" >&2; }
banner(){ printf "\n\033[1;35m══════════════════════════════════════════\033[0m\n"; \
          printf "\033[1;35m  %s\033[0m\n" "$*"; \
          printf "\033[1;35m══════════════════════════════════════════\033[0m\n\n"; }

# ── 1. Check Docker ───────────────────────────────────────────────────────────
banner "Step 1 — Docker check"

if ! command -v docker &>/dev/null; then
  err "Docker CLI not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
  exit 1
fi

if ! docker info &>/dev/null; then
  err "Docker daemon is not running. Please start Docker Desktop and try again."
  exit 1
fi

ok "Docker Desktop is running ($(docker version --format '{{.Server.Version}}' 2>/dev/null || echo 'version unknown'))"

# ── 2. Set up .env ────────────────────────────────────────────────────────────
banner "Step 2 — Environment setup"

if [ ! -f "$ENV_FILE" ]; then
  warn ".env not found — creating from .env.example"
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  ok "Created $ENV_FILE"
fi

# Ensure APP_SECRETS_MASTER_KEY is a real Fernet key (not the placeholder)
CURRENT_KEY=$(grep -E '^APP_SECRETS_MASTER_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '[:space:]')

if [ -z "$CURRENT_KEY" ] || [ "$CURRENT_KEY" = "REPLACE_WITH_FERNET_KEY" ]; then
  warn "Generating a new APP_SECRETS_MASTER_KEY..."
  NEW_KEY=$(docker run --rm python:3.12-slim python -c \
    "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
    || python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null \
    || "")
  if [ -z "$NEW_KEY" ]; then
    err "Could not generate Fernet key. Install Python 3 and run: pip install cryptography"
    err "Then set APP_SECRETS_MASTER_KEY manually in .env"
    exit 1
  fi
  # Replace or append the key in .env
  if grep -qE '^APP_SECRETS_MASTER_KEY=' "$ENV_FILE"; then
    sed -i.bak "s|^APP_SECRETS_MASTER_KEY=.*|APP_SECRETS_MASTER_KEY=$NEW_KEY|" "$ENV_FILE"
    rm -f "$ENV_FILE.bak"
  else
    echo "APP_SECRETS_MASTER_KEY=$NEW_KEY" >> "$ENV_FILE"
  fi
  ok "Generated and saved APP_SECRETS_MASTER_KEY"
fi

ok ".env is ready"

# ── 3. Clean (optional) ───────────────────────────────────────────────────────
if [ "$CLEAN" = true ]; then
  banner "Step 3 — Clean up (--clean flag)"
  warn "Stopping containers and removing all volumes..."
  COMPOSE_ARGS=(-f "$COMPOSE_FILE")
  [ "$OBSERVABILITY" = true ] && COMPOSE_ARGS+=(--profile observability)
  docker compose "${COMPOSE_ARGS[@]}" down -v --remove-orphans 2>/dev/null || true
  ok "Clean complete"
else
  banner "Step 3 — Skipping clean (use --clean to wipe volumes)"
fi

# ── 4. Build images ───────────────────────────────────────────────────────────
banner "Step 4 — Building Docker images"
info "This may take a few minutes on the first run..."

COMPOSE_ARGS=(-f "$COMPOSE_FILE")
[ "$OBSERVABILITY" = true ] && COMPOSE_ARGS+=(--profile observability)

docker compose "${COMPOSE_ARGS[@]}" build --parallel
ok "All images built"

# ── 5. Start services ─────────────────────────────────────────────────────────
banner "Step 5 — Starting services"
docker compose "${COMPOSE_ARGS[@]}" up -d
ok "Services started"

# ── 6. Wait for backend to be healthy ────────────────────────────────────────
banner "Step 6 — Waiting for services to be ready"

BACKEND_URL="http://localhost:8000/health/ready"
FRONTEND_URL="http://localhost:5173"
MAX_WAIT=120  # seconds
INTERVAL=3

info "Waiting for backend at $BACKEND_URL (up to ${MAX_WAIT}s)..."
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    ok "Backend is healthy"
    break
  fi
  printf "  (%ds) backend not ready yet (HTTP %s) — waiting...\n" "$elapsed" "$STATUS"
  sleep $INTERVAL
  elapsed=$((elapsed + INTERVAL))
done

if [ "$STATUS" != "200" ]; then
  err "Backend did not become healthy after ${MAX_WAIT}s"
  err "Check logs with: docker compose -f infra/compose/compose.yaml logs backend"
  exit 1
fi

info "Waiting for frontend at $FRONTEND_URL..."
elapsed=0
while [ $elapsed -lt $MAX_WAIT ]; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    ok "Frontend is healthy"
    break
  fi
  printf "  (%ds) frontend not ready yet (HTTP %s) — waiting...\n" "$elapsed" "$STATUS"
  sleep $INTERVAL
  elapsed=$((elapsed + INTERVAL))
done

if [ "$STATUS" != "200" ]; then
  warn "Frontend did not respond after ${MAX_WAIT}s (may still be compiling)"
fi

# ── 7. Print summary ──────────────────────────────────────────────────────────
banner "Ready!"

printf "\033[1;32m"
echo "  Application URLs:"
echo "  ─────────────────────────────────────────"
echo "  Frontend (Chat UI)   → http://localhost:5173"
echo "  Backend API          → http://localhost:8000"
echo "  API Docs (Swagger)   → http://localhost:8000/docs"
if [ "$OBSERVABILITY" = true ]; then
echo "  Grafana (dashboards) → http://localhost:3000  (admin / admin)"
echo "  Jaeger (traces)      → http://localhost:16686"
echo "  Prometheus (metrics) → http://localhost:9090"
fi
echo "  ─────────────────────────────────────────"
echo ""
echo "  Default login:  admin / ChangeMe123!"
echo ""
echo "  Next step:"
echo "    1. Open http://localhost:5173 in your browser"
echo "    2. Log in with admin / ChangeMe123!"
echo "    3. Go to Admin → OpenAI Key and enter your OpenAI API key"
echo "    4. Upload a document and start chatting!"
echo ""
echo "  To stop:   docker compose -f infra/compose/compose.yaml down"
echo "  To view logs: docker compose -f infra/compose/compose.yaml logs -f"
printf "\033[0m"

# ── 8. Open browser (macOS) ───────────────────────────────────────────────────
if command -v open &>/dev/null; then
  info "Opening browser..."
  sleep 1
  open "http://localhost:5173"
elif command -v xdg-open &>/dev/null; then
  info "Opening browser..."
  sleep 1
  xdg-open "http://localhost:5173"
fi
