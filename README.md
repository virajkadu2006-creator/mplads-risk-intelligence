# MPLADS Risk Intelligence System

This repository contains the MPLADS Risk Intelligence System, an MVP built for the Smart India Hackathon (Problem Statement 26102).

## Architecture

- **Data Pipeline:** Processes raw CSVs, performs data cleaning, normalization, joining, and feature engineering.
- **Rules Engine:** Applies threshold-based rules (Cost Overrun, Delay, Under-Utilization, Trust Compliance, Duplicate Detection).
- **Machine Learning:** Utilizes an Isolation Forest model to flag statistical outliers in project features.
- **Backend:** FastAPI application serving explainable risk scores and project details from a SQLite database (SQLAlchemy).
- **Frontend:** Dashboard for geographic analysis, risk monitoring, and project investigation.

## Quickstart

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Place the dataset files (`recommended_works.csv`, `sanctioned_works.csv`, `payments.csv`) in `data/raw/`.
3. Run the data pipeline (script to be written in Phase 2).
4. Run the backend server (script to be written in Phase 7).
