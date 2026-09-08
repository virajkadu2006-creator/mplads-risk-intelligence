import pytest
import os
import pandas as pd

def test_banned_words_in_alerts():
    """Assert no persisted alert contains accusatory/banned words (Part 6.3)."""
    alerts_path = "data/processed/alerts.parquet"
    if not os.path.exists(alerts_path):
        pytest.skip("alerts.parquet not found yet")
        
    alerts = pd.read_parquet(alerts_path)
    banned = ["fraud", "guilty", "corrupt", "criminal"]
    
    for _, row in alerts.iterrows():
        text = str(row.get("reason_text", "")).lower()
        for b in banned:
            assert b not in text, f"Banned word '{b}' found in alert {row.get('alert_id')}: {text}"

def test_banned_words_in_code():
    """Check Python files in ml/ and backend/ for banned terms in string literals."""
    banned = ["fraud", "guilty", "corrupt", "criminal"]
    check_dirs = ["ml", "backend"]
    
    for d in check_dirs:
        for root, _, files in os.walk(d):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    for idx, line in enumerate(lines, start=1):
                        # Skip comments explaining the banned words rule
                        if "#" in line and "banned" in line.lower():
                            continue
                        clean_line = line.lower()
                        for b in banned:
                            # Avoid false positives if word is part of variable names like antifraud if any
                            assert f'"{b}"' not in clean_line and f"'{b}'" not in clean_line, (
                                f"Banned word literal '{b}' in {file_path}:{idx}: {line.strip()}"
                            )
