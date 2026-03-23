#!/bin/sh
set -e

# Only run database migrations for the API server (default command)
case "$1" in
  gunicorn*)
    alembic upgrade head
    ;;
esac

exec "$@"
