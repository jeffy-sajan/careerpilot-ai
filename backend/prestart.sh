#!/bin/bash
# prestart.sh — Runs before uvicorn starts inside the container.
# 1. Waits for the database to be ready
# 2. Runs Alembic migrations
# 3. Starts the uvicorn server

set -e

echo "⏳ Running database migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
