#!/usr/bin/env bash
# Start or update the development instance using the current checkout.
set -euo pipefail
umask 077
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
mkdir -p .dev-ha
chmod 700 .dev-ha
compose=(docker compose --project-directory "$repo/docker" -f "$repo/docker/docker-compose.yaml")
"${compose[@]}" up -d --force-recreate
if ! "${compose[@]}" wait bootstrap; then
    "${compose[@]}" logs --no-log-prefix bootstrap >&2
    exit 1
fi
"${compose[@]}" logs --no-log-prefix bootstrap
