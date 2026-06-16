#!/usr/bin/env sh
set -eu

PORT="${PORT:-8000}"
echo "Starting Voice Generator API on 0.0.0.0:${PORT}"
exec python -m uvicorn api.app.main:app --host 0.0.0.0 --port "${PORT}"
