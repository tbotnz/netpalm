#!/bin/sh
set -e

# Run database migrations before starting the application
alembic upgrade head

exec "$@"
