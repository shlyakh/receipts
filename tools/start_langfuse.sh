#!/bin/bash
# Start the local Langfuse (Docker) and wait until it answers.
#
#   tools/start_langfuse.sh          start (also starts Docker Desktop if needed)
#   tools/start_langfuse.sh stop     stop the containers (data is kept)
#   tools/start_langfuse.sh status   show the containers
#
# Langfuse lives outside this repository; set LANGFUSE_DIR to override the location.
set -euo pipefail

LANGFUSE_DIR="${LANGFUSE_DIR:-/Users/yuri/work/langfuse}"
URL="${LANGFUSE_URL:-http://localhost:3000}"

if [ ! -f "$LANGFUSE_DIR/docker-compose.yml" ]; then
  echo "No docker-compose.yml in $LANGFUSE_DIR" >&2
  exit 1
fi
cd "$LANGFUSE_DIR"

case "${1:-start}" in
  stop)   docker compose stop; exit 0 ;;
  status) docker compose ps; exit 0 ;;
  start)  ;;
  *)      echo "Usage: $0 [start|stop|status]" >&2; exit 2 ;;
esac

if ! docker info >/dev/null 2>&1; then
  echo "Starting Docker Desktop..."
  open -a Docker
  for _ in $(seq 1 60); do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
  docker info >/dev/null 2>&1 || { echo "Docker did not start within 2 minutes." >&2; exit 1; }
fi

docker compose up -d

echo "Waiting for Langfuse at $URL ..."
for _ in $(seq 1 60); do
  if curl -fsS -o /dev/null "$URL/api/public/health"; then
    echo "Langfuse is up: $URL"
    exit 0
  fi
  sleep 3
done
echo "Containers are started but $URL did not answer within 3 minutes. Check: $0 status" >&2
exit 1
