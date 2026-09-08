import pandas as pd
import numpy as np
import logging
import yaml

logger = logging.getLogger(__name__)

class RiskScorer:
    def __init__(self, config_path="config/thresholds.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def compute_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Computing combined risk scores...")
        weights = self.config['risk_scoring']['weights']
        
        # 1. Cost Factor [0, 2]
        # Only overshoot above 1.0 counts for the raw score addition
        df['cost_factor'] = np.minimum(df['cost_overrun_ratio'].fillna(0), 2.0)
        df['cost_contribution'] = weights['cost'] * np.clip(df['cost_factor'] - 1.0, 0, 1)
        
        # 2. Delay Factor [0, 2]
        df['delay_factor'] = np.minimum(df['delay_days'].clip(lower=0) / 365.0, 2.0)
        df['delay_contribution'] = weights['delay'] * np.clip(df['delay_factor'] - 1.0, 0, 1)
        
        # 3. ML Factor [0, 1]
        df['ml_factor'] = df['ml_risk_score'] / 100.0
        df['ml_contribution'] = weights['ml'] * np.clip(df['ml_factor'], 0, 1)
        
        # 4. Compliance Factor {0, 2}
        has_trust_or_exact_dup = df['rule_flag_trust'] | (df['duplicate_confidence'] == 'exact')
        df['compliance_factor'] = np.where(has_trust_or_exact_dup, 2.0, 0.0)
        df['compliance_contribution'] = weights['compliance'] * (df['compliance_factor'] / 2.0)
        
        # 5. Under-utilization Contribution [0, 15]
        # Added if under_utilization rule fires
        df['under_utilization_contribution'] = np.where(df['rule_flag_under_utilization'], weights.get('under_utilization', 15), 0.0)
        
        # Total Raw Score
        df['raw_risk_score'] = (df['cost_contribution'] + 
                                df['delay_contribution'] + 
                                df['ml_contribution'] + 
                                df['compliance_contribution'] + 
                                df['under_utilization_contribution'])
                                
        # Cap to 100
        df['risk_score'] = np.clip(df['raw_risk_score'].fillna(0), 0, 100).round().astype(int)
        
        # Categories
        bounds = self.config['risk_scoring']['category_bounds']
        
        def categorize(score):
            if score <= bounds['low']: return "Low"
            elif score <= bounds['medium']: return "Medium"
            elif score <= bounds['high']: return "High"
            else: return "Critical"
            
        df['risk_category'] = df['risk_score'].apply(categorize)
        logger.info("Risk scoring complete.")
        return df

class Explainer:
    def __init__(self):
        pass
        
    def add_explanations(self, df: pd.DataFrame, alerts_df: pd.DataFrame):
        logger.info("Generating explanation strings...")
        # Explanations are mostly mapped in alerts already from rules
        # Add ML outlier explanations
        ml_mask = df['ml_factor'] > 0.5
        new_alerts = []
        for idx, row in df[ml_mask].iterrows():
            new_alerts.append({
                "alert_id": "ml_" + str(idx),
                "project_id": row['project_id'],
                "alert_type": "ML_OUTLIER",
                "severity": "High" if row['ml_factor'] > 0.75 else "Medium",
                "reason_text": f"This project is statistically unusual compared with similar {row['work_category']} works (anomaly strength {row['ml_factor']:.2f}).",
                "rule_version": "isolation_forest_v1",
                "triggered_at": pd.Timestamp.utcnow().isoformat() + "Z"
            })
            
        if new_alerts:
            new_alerts_df = pd.DataFrame(new_alerts)
            alerts_df = pd.concat([alerts_df, new_alerts_df], ignore_index=True)
            
        return df, alerts_df
