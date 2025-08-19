#!/bin/bash
set -e

# Run FastAPI on port 8000 in the background
uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8000 &

# Run Dash dashboard on port 8050
python dashboard/app.py --host 0.0.0.0 --port 8050
