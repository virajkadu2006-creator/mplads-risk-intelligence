import pytest
import os
import pandas as pd
import json

def test_data_pipeline_outputs():
    """Verify presence and schema integrity of processed parquet files."""
    assert os.path.exists("data/processed/projects_analytical.parquet")
    assert os.path.exists("data/processed/alerts.parquet")
    assert os.path.exists("data/processed/data_quality_report.json")
    
    projects = pd.read_parquet("data/processed/projects_analytical.parquet")
    alerts = pd.read_parquet("data/processed/alerts.parquet")
    
    # Check row counts
    assert len(projects) > 0
    assert len(alerts) > 0
    
    # Check essential columns in analytical table
    required_cols = [
        "project_id", "state", "district", "mp_name", "work_name",
        "sanction_amount", "amount_spent", "cost_overrun_ratio",
        "delay_days", "ml_risk_score", "risk_score", "risk_category"
    ]
    for col in required_cols:
        assert col in projects.columns, f"Missing required column: {col}"
        
    # Check score bounds
    assert projects["risk_score"].min() >= 0
    assert projects["risk_score"].max() <= 100
    
    # Check categories
    valid_categories = {"Low", "Medium", "High", "Critical"}
    assert set(projects["risk_category"].unique()).issubset(valid_categories)
    
    # Check data quality report
    with open("data/processed/data_quality_report.json", "r") as f:
        report = json.load(f)
    assert "total_rows_ingested" in report
    assert "join_coverage_pct" in report
