import os
import requests
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ---------------------------------------------------------------------------
# Load MP name + constituency lookup directly from raw CSV (always up to date)
# This bypasses any stale backend DB and ensures real names are always shown.
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_name_lookup():
    """Returns dict: unique_work_number -> {mp_name, constituency}"""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "recommended_works.csv")
        csv_path = os.path.abspath(csv_path)
        df = pd.read_csv(csv_path, usecols=["unique_work_number", "mp_name", "constituency"])
        # Build project_id -> names dict (project_id == unique_work_number in the DB)
        return {
            row["unique_work_number"]: {
                "mp_name": row["mp_name"],
                "constituency": row["constituency"]
            }
            for _, row in df.iterrows()
        }
    except Exception:
        return {}

def apply_name_lookup(df, lookup):
    """Replace mp_name and constituency in a dataframe using the CSV lookup."""
    if lookup and "project_id" in df.columns:
        df = df.copy()
        df["mp_name"] = df["project_id"].map(lambda pid: lookup.get(pid, {}).get("mp_name") or df.loc[df["project_id"]==pid, "mp_name"].values[0] if pid in lookup else df.loc[df["project_id"]==pid, "mp_name"].values[0])
        df["constituency"] = df["project_id"].map(lambda pid: lookup.get(pid, {}).get("constituency") or "")
    return df

@st.cache_data(ttl=15)
def fetch_api(endpoint, params=None):
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

def post_api(endpoint, payload):
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10)
        response.raise_for_status()
        st.cache_data.clear()
        return response.json()
    except Exception as e:
        st.error(f"Action failed: {e}")
        return None
