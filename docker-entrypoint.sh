#!/bin/bash
set -e

mkdir -p /app/logs /app/data/uploads

if [ "$SERVICE" = "api" ]; then
  echo "Waiting for MongoDB..."
  until (echo > /dev/tcp/mongodb/27017) 2>/dev/null; do
    sleep 1
  done
  echo "MongoDB is ready"
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000

elif [ "$SERVICE" = "ui" ]; then
  exec streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

else
  echo "ERROR: SERVICE env var must be 'api' or 'ui'"
  exit 1
fi
