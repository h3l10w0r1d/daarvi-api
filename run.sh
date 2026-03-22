#!/bin/bash
set -e
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
