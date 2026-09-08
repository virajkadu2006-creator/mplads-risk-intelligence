#!/bin/bash
# Start backend API in background
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to be ready
sleep 2

# Start Streamlit frontend
python -m streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
