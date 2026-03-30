#!/usr/bin/env bash
set -e

# Ensure the script works no matter which directory Render starts from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-1}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

if [[ -d "${PROJECT_ROOT}/lafzloom" ]]; then
  APP_MODULE="lafzloom.wsgi:application"
else
  echo "Could not find Django project package (expected lafzloom/)." >&2
  exit 1
fi

exec gunicorn "${APP_MODULE}" \
  --bind "0.0.0.0:${PORT}" \
  --workers "${WEB_CONCURRENCY}" \
  --timeout "${GUNICORN_TIMEOUT}"
