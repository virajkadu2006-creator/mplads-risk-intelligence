import pytest
import pandas as pd
from ml.rules import RuleEngine

@pytest.fixture
def rule_engine():
    return RuleEngine("config/thresholds.yaml")

def test_cost_overrun_rule(rule_engine):
    df = pd.DataFrame([
        {
            "project_id": "P_OVERRUN",
            "cost_overrun_ratio": 1.35,
            "overrun_pct": 35.0,
            "amount_spent": 1350000.0,
            "sanction_amount": 1000000.0,
            "work_status": "In Progress"
        },
        {
            "project_id": "P_NORMAL",
            "cost_overrun_ratio": 1.02,
            "overrun_pct": 2.0,
            "amount_spent": 1020000.0,
            "sanction_amount": 1000000.0,
            "work_status": "Completed"
        }
    ])
    rule_engine.apply_cost_overrun(df)
    assert df.loc[df["project_id"] == "P_OVERRUN", "rule_flag_cost_overrun"].iloc[0] == True
    # The normal completed project within tolerance band should NOT fire
    assert df.loc[df["project_id"] == "P_NORMAL", "rule_flag_cost_overrun"].iloc[0] == False

def test_under_utilization_age_gate(rule_engine):
    df = pd.DataFrame([
        {
            "project_id": "P_OLD_UNSPENT",
            "project_age_days": 250,
            "underutilization_ratio": 0.95,
            "sanction_amount": 1000000.0,
            "work_status": "In Progress"
        },
        {
            "project_id": "P_NEW_UNSPENT",
            "project_age_days": 45,  # Too young to flag (<180 days)
            "underutilization_ratio": 0.95,
            "sanction_amount": 1000000.0,
            "work_status": "In Progress"
        }
    ])
    rule_engine.apply_under_utilization(df)
    assert df.loc[df["project_id"] == "P_OLD_UNSPENT", "rule_flag_under_utilization"].iloc[0] == True
    assert df.loc[df["project_id"] == "P_NEW_UNSPENT", "rule_flag_under_utilization"].iloc[0] == False

def test_delay_rule(rule_engine):
    df = pd.DataFrame([
        {
            "project_id": "P_DELAYED",
            "delay_days": 400,
            "work_status": "In Progress"
        },
        {
            "project_id": "P_ON_TIME",
            "delay_days": 200,
            "work_status": "In Progress"
        },
        {
            "project_id": "P_COMPLETED_OLD",
            "delay_days": 500,
            "work_status": "Completed"  # Completed projects should not flag delay
        }
    ])
    rule_engine.apply_delay(df)
    assert df.loc[df["project_id"] == "P_DELAYED", "rule_flag_delay"].iloc[0] == True
    assert df.loc[df["project_id"] == "P_ON_TIME", "rule_flag_delay"].iloc[0] == False
    assert df.loc[df["project_id"] == "P_COMPLETED_OLD", "rule_flag_delay"].iloc[0] == False

def test_trust_compliance_rule(rule_engine):
    df = pd.DataFrame([
        {
            "project_id": "P_TRUST_BREACH",
            "total_trust_amount_by_mp_year": 15000000.0,  # 1.5 Cr > 1.0 Cr cap
            "financial_year": 2023
        },
        {
            "project_id": "P_TRUST_OK",
            "total_trust_amount_by_mp_year": 5000000.0,   # 50 Lakh <= 1.0 Cr cap
            "financial_year": 2023
        }
    ])
    rule_engine.apply_trust_compliance(df)
    assert df.loc[df["project_id"] == "P_TRUST_BREACH", "rule_flag_trust"].iloc[0] == True
    assert df.loc[df["project_id"] == "P_TRUST_OK", "rule_flag_trust"].iloc[0] == False
