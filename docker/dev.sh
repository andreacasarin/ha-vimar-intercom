#!/usr/bin/env bash
# Start or update the development instance using the current checkout.
set -euo pipefail
umask 077
repo=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo"
mkdir -p .dev-ha
chmod 700 .dev-ha
docker compose up -d --force-recreate
if ! docker compose wait bootstrap; then
    docker compose logs --no-log-prefix bootstrap >&2
    exit 1
fi
docker compose logs --no-log-prefix bootstrap
