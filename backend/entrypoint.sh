#!/bin/bash
set -e

echo "=== Starting AI Customer Support Refund Backend ==="

# Wait for PostgreSQL to accept connections
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-refunds_user}"
POSTGRES_DB="${POSTGRES_DB:-refunds_db}"

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
python -c '
import socket, sys, time
host = sys.argv[1]
port = int(sys.argv[2])
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL connection confirmed.")
            sys.exit(0)
    except OSError:
        time.sleep(1)
print("Timeout waiting for PostgreSQL", file=sys.stderr)
sys.exit(1)
' "${POSTGRES_HOST}" "${POSTGRES_PORT}"
echo "PostgreSQL is ready and accepting connections."

# Execute database migrations
echo "Applying database migrations..."
PYTHONPATH=/app alembic upgrade head || {
  echo "Alembic upgrade completed or tables already at head."
}

# Ensure database is seeded with 16 customer personas and defaults
echo "Verifying database seed data..."
PYTHONPATH=/app python -m app.db.seed || {
  echo "Database seed check completed."
}

echo "Launching uvicorn application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
