# 🏛️ MPLADS Risk Intelligence System

[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Decision-Support & Risk Detection System for **Smart India Hackathon (Problem Statement 26102)**. Analyzes Member of Parliament Local Area Development Scheme (MPLADS) projects to identify delay anomalies, cost overruns, under-utilization, duplicate works, and statistical outliers using machine learning.

---

## 🌟 Key Features

- **📊 Executive Overview:** Real-time KPI summaries, risk distribution breakdown, and data quality metrics.
- **🔍 Risk Monitor:** Multi-criteria filtering (State, Category, Severity) with search and CSV export functionality.
- **📁 Project Investigation Dossier:** Comprehensive deep-dives with financial analysis, peer group percentile ranking, objective alerts, and auditor notes tracking.
- **🗺️ Geographic Risk Distribution:** Interactive state-level anomaly density and funding allocation maps.
- **🧠 ML Outlier Detection:** Unsupervised Isolation Forest model detecting multivariate statistical anomalies.

---

## 🚀 One-Click Deployment Guides

### Option 1: Deploy on Render (Recommended)

1. Fork or push this repository to GitHub.
2. Log in to [Render](https://render.com/).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository `virajkadu2006-creator/mplads-risk-intelligence`.
5. Render will automatically detect `render.yaml` with the following configuration:
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `bash start.sh`
6. Click **Deploy Web Service**!

---

### Option 2: Deploy on Streamlit Community Cloud

1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click **New app**.
3. Select your repository, branch (`main`), and set Main file path to: `frontend/app.py`.
4. Click **Deploy!** 
*(Note: `frontend/app.py` automatically initializes the FastAPI backend server in a background thread if not already running!)*

---

### Option 3: Deploy using Docker / Railway / Koyeb

```bash
# Build Docker image
docker build -t mplads-risk-intelligence .

# Run container
docker run -p 8501:8501 mplads-risk-intelligence
```
Access the dashboard at `http://localhost:8501`.

---

## 💻 Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/virajkadu2006-creator/mplads-risk-intelligence.git
cd mplads-risk-intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch both Backend API & Streamlit Dashboard
bash start.sh
# Or on Windows PowerShell:
# python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
# python -m streamlit run frontend/app.py
```

- **Frontend Dashboard:** `http://localhost:8501`
- **FastAPI Interactive Docs:** `http://localhost:8000/docs`

---

## 📁 Repository Structure

```
.
├── backend/               # FastAPI backend & database models
│   ├── main.py            # API routes and database connections
│   └── routes/            # Route modules
├── frontend/              # Streamlit analytical dashboard
│   └── app.py             # Main interactive dashboard UI
├── ml/                    # Machine Learning pipeline
│   ├── anomaly_model.py   # Isolation Forest model training/inference
│   ├── cleaning.py        # Data cleaning & normalization
│   └── rules.py           # Threshold-based anomaly detection rules
├── data/                  # Raw and processed dataset files
├── scripts/               # Pipeline execution scripts & DB seeders
├── mplads.db              # SQLite database (pre-seeded with analytical data)
├── Dockerfile             # Container configuration
├── render.yaml            # Render deployment manifest
├── Procfile               # Heroku/Render process declaration
├── start.sh               # Production startup script
└── requirements.txt       # Python dependency requirements
```
