import pandas as pd
import logging
import uuid
import datetime
import yaml

logger = logging.getLogger(__name__)

class RuleEngine:
    def __init__(self, config_path="config/thresholds.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.alerts = []
        self.rule_version = "v1"

    def apply_cost_overrun(self, df: pd.DataFrame):
        if 'rule_flag_cost_overrun' not in df.columns:
            df['rule_flag_cost_overrun'] = False
        threshold = self.config['cost_overrun']['ratio_threshold']
        tolerance = self.config['cost_overrun']['tolerance_band']
        
        mask = df['cost_overrun_ratio'] > threshold
        
        # Apply tolerance if completed
        completed_mask = df['work_status'] == 'Completed'
        in_tolerance = (df['cost_overrun_ratio'] <= 1.0 + tolerance)
        mask = mask & ~(completed_mask & in_tolerance)
        
        for idx, row in df[mask].iterrows():
            self._add_alert(row['project_id'], "COST_OVERRUN", "High", 
                            f"Cost exceeded the sanctioned amount by {row['overrun_pct']:.1f}% (Rs.{row['amount_spent']} vs Rs.{row['sanction_amount']} sanctioned).")
            df.at[idx, 'rule_flag_cost_overrun'] = True

    def apply_under_utilization(self, df: pd.DataFrame):
        if 'rule_flag_under_utilization' not in df.columns:
            df['rule_flag_under_utilization'] = False
        age_thresh = self.config['under_utilization']['age_threshold_days']
        ratio_thresh = self.config['under_utilization']['ratio_threshold']
        
        mask = (df['project_age_days'] > age_thresh) & (df['underutilization_ratio'] > ratio_thresh) & (df['work_status'] != 'Completed')
        for idx, row in df[mask].iterrows():
            spent_pct = (1 - row['underutilization_ratio']) * 100
            self._add_alert(row['project_id'], "UNDER_UTILIZED", "Medium", 
                            f"Only {spent_pct:.1f}% of the sanctioned Rs.{row['sanction_amount']} has been spent after {row['project_age_days']} days.")
            df.at[idx, 'rule_flag_under_utilization'] = True

    def apply_delay(self, df: pd.DataFrame):
        if 'rule_flag_delay' not in df.columns:
            df['rule_flag_delay'] = False
        thresh = self.config['delay']['threshold_days']
        mask = (df['delay_days'] > thresh) & (df['work_status'] != 'Completed')
        for idx, row in df[mask].iterrows():
            self._add_alert(row['project_id'], "DELAYED", "Medium", 
                            f"Project has remained incomplete for {row['delay_days']} days, beyond the ~1-year completion norm.")
            df.at[idx, 'rule_flag_delay'] = True

    def apply_duplicate(self, df: pd.DataFrame):
        if 'rule_flag_duplicate' not in df.columns:
            df['rule_flag_duplicate'] = False
        mask = df['duplicate_confidence'].notnull()
        for idx, row in df[mask].iterrows():
            severity = "Critical" if row['duplicate_confidence'] == "exact" else "High"
            self._add_alert(row['project_id'], "POSSIBLE_DUPLICATE", severity, 
                            f"Possible duplicate/overlapping work detected: {row['duplicate_confidence']} match with group {row['duplicate_group_id']} in the same {row['district']}/{row['constituency']}.")
            df.at[idx, 'rule_flag_duplicate'] = True

    def apply_trust_compliance(self, df: pd.DataFrame):
        if 'rule_flag_trust' not in df.columns:
            df['rule_flag_trust'] = False
        cap = self.config['trust_compliance']['mp_annual_aggregate_cap']
        mask = df['total_trust_amount_by_mp_year'] > cap
        for idx, row in df[mask].iterrows():
            self._add_alert(row['project_id'], "TRUST_COMPLIANCE", "High", 
                            f"Trust/Society-linked recommendations for this MP total Rs.{row['total_trust_amount_by_mp_year']} in {row['financial_year']}, exceeding the configured cap of Rs.{cap}.")
            df.at[idx, 'rule_flag_trust'] = True

    def _add_alert(self, project_id, alert_type, severity, text):
        self.alerts.append({
            "alert_id": str(uuid.uuid4()),
            "project_id": project_id,
            "alert_type": alert_type,
            "severity": severity,
            "reason_text": text,
            "rule_version": self.rule_version,
            "triggered_at": datetime.datetime.utcnow().isoformat() + "Z"
        })

    def run(self, df: pd.DataFrame) -> (pd.DataFrame, pd.DataFrame):
        logger.info("Running Rule Engine...")
        df['rule_flag_cost_overrun'] = False
        df['rule_flag_under_utilization'] = False
        df['rule_flag_delay'] = False
        df['rule_flag_duplicate'] = False
        df['rule_flag_trust'] = False

        self.apply_cost_overrun(df)
        self.apply_under_utilization(df)
        self.apply_delay(df)
        self.apply_duplicate(df)
        self.apply_trust_compliance(df)
        
        alerts_df = pd.DataFrame(self.alerts)
        logger.info(f"Rule Engine complete. Generated {len(alerts_df)} alerts.")
        return df, alerts_df
