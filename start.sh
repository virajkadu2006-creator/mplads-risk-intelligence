#!/bin/bash
# Dynamic port configuration (uses PORT injected by cloud providers like Render/Heroku, default 8501)
PORT=${PORT:-8501}

echo "Starting FastAPI backend server on port 8000..."
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &

# Wait for backend to initialize
sleep 3

echo "Starting Streamlit frontend on port $PORT..."
python -m streamlit run frontend/app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true

