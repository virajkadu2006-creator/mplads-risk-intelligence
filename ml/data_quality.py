import os
import json
import logging
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityMonitor:
    def __init__(self, run_id):
        self.run_id = run_id
        self.generated_at = datetime.utcnow().isoformat() + "Z"
        self.report = {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "total_rows_ingested": {},
            "rows_rejected": {"count": 0, "reasons": {}},
            "unmatched_records": {"count": 0},
            "join_coverage_pct": 0.0,
            "fields_with_high_nullness": []
        }
        
    def record_ingestion(self, file_type: str, count: int):
        self.report["total_rows_ingested"][file_type] = count
        
    def record_rejection(self, reason: str, count: int):
        if count == 0:
            return
        self.report["rows_rejected"]["count"] += count
        if reason not in self.report["rows_rejected"]["reasons"]:
            self.report["rows_rejected"]["reasons"][reason] = 0
        self.report["rows_rejected"]["reasons"][reason] += count
        
    def record_unmatched(self, count: int):
        self.report["unmatched_records"]["count"] += count
        
    def calculate_coverage(self, final_joined_count: int):
        total_sanc = self.report["total_rows_ingested"].get("sanctioned", 0)
        total_rec = self.report["total_rows_ingested"].get("recommended", 0)
        # Using sanctioned as the base denominator if present, else recommended
        base = total_sanc if total_sanc > 0 else total_rec
        
        if base > 0:
            self.report["join_coverage_pct"] = round((final_joined_count / base) * 100, 2)
        else:
            self.report["join_coverage_pct"] = 0.0

    def calculate_nullness(self, df: pd.DataFrame):
        null_counts = df.isnull().sum()
        total_rows = len(df)
        if total_rows == 0:
            return
            
        for col, null_cnt in null_counts.items():
            null_pct = (null_cnt / total_rows) * 100
            if null_pct > 10.0:  # Threshold for high nullness
                self.report["fields_with_high_nullness"].append({
                    "field": col,
                    "null_pct": round(null_pct, 2)
                })

    def save_report(self, filepath="data/processed/data_quality_report.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.report, f, indent=2)
        logger.info(f"Data quality report saved to {filepath}")
        
    def print_summary(self):
        logger.info(f"--- Data Quality Summary (Run: {self.run_id}) ---")
        logger.info(f"Ingested: {self.report['total_rows_ingested']}")
        logger.info(f"Rejected Rows: {self.report['rows_rejected']['count']} ({self.report['rows_rejected']['reasons']})")
        logger.info(f"Unmatched Records: {self.report['unmatched_records']['count']}")
        logger.info(f"Join Coverage: {self.report['join_coverage_pct']}%")
