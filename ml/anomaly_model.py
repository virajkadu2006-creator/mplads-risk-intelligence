import pandas as pd
import numpy as np
import logging
import os
import yaml
import json
import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib

logger = logging.getLogger(__name__)

class AnomalyModel:
    def __init__(self, config_path="config/thresholds.yaml", model_dir="ml/models"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.features = [
            "cost_overrun_ratio",
            "underutilization_ratio",
            "delay_days",
            "sanction_amount_log",
            "num_payments",
            "max_vendor_share",
            "duplicate_similarity_max"
        ]
        
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Preprocessing for ML...")
        # Deep copy to avoid SettingWithCopyWarning
        ml_df = df.copy()
        
        # Create log sanctioned amount
        ml_df['sanction_amount_log'] = np.log1p(ml_df['sanction_amount'].fillna(0))
        
        # Imputation
        for feat in self.features:
            if feat not in ml_df.columns:
                ml_df[feat] = 0.0
            
            ml_df[f'is_imputed_{feat}'] = ml_df[feat].isnull()
            # Simple global median imputation
            median_val = ml_df[feat].median()
            if pd.isnull(median_val):
                median_val = 0.0
            ml_df[feat] = ml_df[feat].fillna(median_val)
            
        return ml_df

    def train_and_score(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Training Isolation Forest...")
        ml_df = self.preprocess(df)
        X = ml_df[self.features].copy()
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        contamination = self.config['ml']['contamination']
        random_state = self.config['ml']['random_state']
        n_estimators = self.config['ml']['n_estimators']
        
        iso_forest = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state
        )
        
        iso_forest.fit(X_scaled)
        
        # Score
        raw_score = iso_forest.decision_function(X_scaled)
        ml_anomaly = -raw_score
        
        # Normalize to 0-100
        min_max = MinMaxScaler(feature_range=(0, 100))
        ml_risk_0_100 = min_max.fit_transform(ml_anomaly.reshape(-1, 1)).flatten()
        
        df['ml_anomaly_score_raw'] = raw_score
        df['ml_risk_score'] = ml_risk_0_100
        df['model_version'] = "isolation_forest_v1"
        
        # Save model and metadata
        model_path = os.path.join(self.model_dir, "isolation_forest_v1.joblib")
        joblib.dump(iso_forest, model_path)
        
        metadata = {
            "model_version": "isolation_forest_v1",
            "trained_at": datetime.datetime.utcnow().isoformat() + "Z",
            "feature_list": self.features,
            "contamination": contamination,
            "random_state": random_state,
            "dataset_row_count": len(df),
            "normalization_bounds": {
                "min": float(min_max.data_min_[0]),
                "max": float(min_max.data_max_[0])
            }
        }
        with open(os.path.join(self.model_dir, "model_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("ML scoring complete.")
        return df
