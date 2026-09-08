import pytest
import pandas as pd
from ml.risk_scoring import RiskScorer

@pytest.fixture
def scorer():
    return RiskScorer("config/thresholds.yaml")

def test_part_5_5_worked_example(scorer):
    """
    Part 5.5 Worked Example:
    Sanction = Rs. 10,00,000
    Spent = Rs. 16,00,000 (expenditure_ratio = 1.6)
    Delay = 240 days (under 365-day norm -> 0 delay contribution)
    ML anomaly factor = 0.8 (normalized score = 80.0 -> ML contribution = 20.0)
    Compliance = 0
    Expected Risk Score = 35 (Medium)
    """
    df = pd.DataFrame([{
        "project_id": "TEST_WORKED_EX",
        "sanction_amount": 1000000.0,
        "amount_spent": 1600000.0,
        "cost_overrun_ratio": 1.6,
        "delay_days": 240,
        "ml_risk_score": 80.0,
        "rule_flag_trust": False,
        "duplicate_confidence": None,
        "rule_flag_under_utilization": False
    }])
    result = scorer.compute_scores(df)
    assert result["risk_score"].iloc[0] == 35
    assert result["risk_category"].iloc[0] == "Medium"
    assert result["cost_contribution"].iloc[0] == pytest.approx(15.0)
    assert result["delay_contribution"].iloc[0] == pytest.approx(0.0)
    assert result["ml_contribution"].iloc[0] == pytest.approx(20.0)
    assert result["compliance_contribution"].iloc[0] == pytest.approx(0.0)

def test_zero_risk_project(scorer):
    """A completely normal project within budget and timeline."""
    df = pd.DataFrame([{
        "project_id": "TEST_ZERO",
        "sanction_amount": 500000.0,
        "amount_spent": 450000.0,
        "cost_overrun_ratio": 0.9,
        "delay_days": 100,
        "ml_risk_score": 10.0,
        "rule_flag_trust": False,
        "duplicate_confidence": None,
        "rule_flag_under_utilization": False
    }])
    result = scorer.compute_scores(df)
    assert result["risk_score"].iloc[0] <= 10
    assert result["risk_category"].iloc[0] == "Low"

def test_critical_risk_project(scorer):
    """Severe overrun, massive delay, high ML anomaly, and hard compliance breach."""
    df = pd.DataFrame([{
        "project_id": "TEST_CRITICAL",
        "sanction_amount": 1000000.0,
        "amount_spent": 2500000.0,
        "cost_overrun_ratio": 2.5,
        "delay_days": 800,
        "ml_risk_score": 100.0,
        "rule_flag_trust": True,
        "duplicate_confidence": "exact",
        "rule_flag_under_utilization": False
    }])
    result = scorer.compute_scores(df)
    assert result["risk_score"].iloc[0] == 100
    assert result["risk_category"].iloc[0] == "Critical"
