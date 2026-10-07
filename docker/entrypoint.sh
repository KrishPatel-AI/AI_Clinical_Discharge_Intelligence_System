#!/bin/sh
set -e

# Wait for PostgreSQL if DATABASE_URL points to a PostgreSQL instance
if echo "$DATABASE_URL" | grep -q "^postgres"; then
  echo "Verifying database readiness..."
  python - <<'EOF'
import os
import sys
import time
from sqlalchemy import create_engine, text

url = os.getenv("DATABASE_URL", "")
max_retries = 30
for i in range(max_retries):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successfully established.")
        sys.exit(0)
    except Exception as exc:
        print(f"Waiting for database ({i + 1}/{max_retries}): {exc}")
        time.sleep(2)
print("Timeout waiting for database connection.")
sys.exit(1)
EOF
fi

# Ensure guideline vector index is present
echo "Verifying guideline vector index..."
python knowledge_base/ingest.py

# Apply versioned database migrations
echo "Applying database migrations..."
alembic upgrade head

# Pull model if requested and Ollama is reachable
if [ -n "$OLLAMA_BASE_URL" ] && [ "$PULL_MODELS_ON_STARTUP" = "1" ]; then
  echo "Checking Ollama model availability..."
  curl -s -X POST "$OLLAMA_BASE_URL/api/pull" \
    -d "{\"name\":\"${OLLAMA_MODEL:-llama3.2:3b}\",\"stream\":false}" || true
fi

echo "Starting application service..."
exec "$@"
