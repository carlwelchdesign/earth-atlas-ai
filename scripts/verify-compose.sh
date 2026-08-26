#!/bin/sh
set -eu

compose_files="-f compose.yaml"
if [ "${ECHOATLAS_VERIFY_PREPARED:-0}" = "1" ]; then
  compose_files="$compose_files -f compose.prepared.yaml"
fi

cleanup() {
  docker compose $compose_files down --remove-orphans
}
trap cleanup EXIT INT TERM

docker compose $compose_files config --quiet
docker compose $compose_files build
docker compose $compose_files up --detach --wait --wait-timeout 120

curl --fail --silent --show-error http://127.0.0.1:${ECHOATLAS_API_PORT:-8000}/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:${ECHOATLAS_WEB_PORT:-8080}/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:${ECHOATLAS_WEB_PORT:-8080}/ >/dev/null

docker compose $compose_files ps
