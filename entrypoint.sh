#!/bin/sh
set -e

echo "Waiting for DB to be ready..."
# 若需要，可在此加入等待 DB 的程式碼。但 docker-compose 的 healthcheck 已可確保順序。

echo "Apply database migrations"
python manage.py migrate --noinput

echo "Collect static files"
python manage.py collectstatic --noinput || true

echo "Starting container CMD"
exec "$@"
