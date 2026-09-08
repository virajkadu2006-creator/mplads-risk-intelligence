import pandas as pd
import numpy as np
import logging
import os
import yaml
from rapidfuzz import process, fuzz

logger = logging.getLogger(__name__)

class FeatureEngineer:
    def __init__(self, processed_dir="data/processed", config_path="config/thresholds.yaml"):
        self.processed_dir = processed_dir
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
    def engineer_financial_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Engineering financial features...")
        # Amount spent default to 0 if null and work is sanctioned
        df['amount_spent'] = df['amount_spent'].fillna(0)
        
        # Cost Overrun
        # Only if sanction_amount > 0
        sanc_valid = df['sanction_amount'] > 0
        df['cost_overrun_ratio'] = np.where(sanc_valid, df['amount_spent'] / df['sanction_amount'], np.nan)
        df['overrun_amount'] = np.where(sanc_valid, df['amount_spent'] - df['sanction_amount'], np.nan)
        df['overrun_pct'] = np.where(sanc_valid, (df['overrun_amount'] / df['sanction_amount']) * 100, np.nan)
        
        # Under Utilization
        df['underutilization_ratio'] = np.where(sanc_valid, (df['sanction_amount'] - df['amount_spent']) / df['sanction_amount'], np.nan)
        
        # Payments
        if 'num_payments' not in df.columns:
            df['num_payments'] = np.where(df['amount_spent'] > 0, 1, 0)
        df['avg_payment_amount'] = np.where(df['num_payments'] > 0, df['amount_spent'] / df['num_payments'], 0)
        
        return df

    def engineer_temporal_features(self, df: pd.DataFrame, reference_date=None) -> pd.DataFrame:
        logger.info("Engineering temporal features...")
        if reference_date is None:
            reference_date = pd.Timestamp.now()
        else:
            reference_date = pd.to_datetime(reference_date)
            
        df['reference_date'] = reference_date
        
        # Delay
        df['delay_days'] = (df['reference_date'] - df['sanction_date']).dt.days
        df['is_overdue'] = df['delay_days'] > self.config['delay']['threshold_days']
        
        # Age
        df['project_age_days'] = df['delay_days']
        
        # Fix missing values: 0 for delay if not sanctioned or date missing
        # We will handle imputation in ML phase, but rules need to handle nan
        return df

    def engineer_trust_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Engineering trust features...")
        keywords = ['trust', 'society', 'samiti', 'sangh', 'ngo']
        pattern = '|'.join(keywords)
        
        # is_trust_or_society
        mask_agency = df['implementing_agency'].str.lower().str.contains(pattern, na=False)
        mask_name = df['work_name'].str.lower().str.contains(pattern, na=False)
        df['is_trust_or_society'] = (mask_agency | mask_name).astype(int)
        
        # Aggregate by MP and Financial Year
        # For demo, assume all in same FY or extract FY from sanction_date
        df['financial_year'] = df['sanction_date'].dt.year.fillna(2023).astype(int)
        
        trust_amounts = df[df['is_trust_or_society'] == 1].groupby(['mp_name', 'financial_year'])['sanction_amount'].sum().reset_index()
        trust_amounts.rename(columns={'sanction_amount': 'total_trust_amount_by_mp_year'}, inplace=True)
        
        df = pd.merge(df, trust_amounts, on=['mp_name', 'financial_year'], how='left')
        df['total_trust_amount_by_mp_year'] = df['total_trust_amount_by_mp_year'].fillna(0)
        return df

    def engineer_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Engineering duplicate similarities...")
        df['duplicate_similarity_max'] = 0.0
        df['duplicate_group_id'] = None
        df['duplicate_confidence'] = None
        
        # Group by district, constituency, category
        groups = df.groupby(['district', 'constituency', 'work_category'])
        
        dup_threshold = self.config['duplicate_detection']['similarity_threshold']
        
        group_id_counter = 1
        
        for _, group in groups:
            if len(group) < 2:
                continue
            
            names = group['work_name_normalized'].tolist()
            indices = group.index.tolist()
            
            for i, name1 in enumerate(names):
                for j, name2 in enumerate(names):
                    if i >= j: continue
                    score = fuzz.token_sort_ratio(name1, name2)
                    if score >= dup_threshold:
                        idx1 = indices[i]
                        idx2 = indices[j]
                        df.at[idx1, 'duplicate_similarity_max'] = max(df.at[idx1, 'duplicate_similarity_max'], score)
                        df.at[idx2, 'duplicate_similarity_max'] = max(df.at[idx2, 'duplicate_similarity_max'], score)
                        
                        df.at[idx1, 'duplicate_group_id'] = f"DUP_{group_id_counter}"
                        df.at[idx2, 'duplicate_group_id'] = f"DUP_{group_id_counter}"
                        
                        if score == 100:
                            conf = 'exact'
                        elif score >= 90:
                            conf = 'high'
                        else:
                            conf = 'medium'
                            
                        df.at[idx1, 'duplicate_confidence'] = conf
                        df.at[idx2, 'duplicate_confidence'] = conf
                
            group_id_counter += 1
            
        return df

    def run(self, df: pd.DataFrame, reference_date=None) -> pd.DataFrame:
        df = self.engineer_financial_features(df)
        df = self.engineer_temporal_features(df, reference_date)
        df = self.engineer_trust_features(df)
        df = self.engineer_duplicates(df)
        
        # Ensure all columns required for ml are present
        if 'max_vendor_share' not in df.columns:
            df['max_vendor_share'] = np.nan
            
        df.to_parquet(os.path.join(self.processed_dir, "projects_analytical.parquet"))
        logger.info(f"Feature engineering complete. File saved to {self.processed_dir}/projects_analytical.parquet")
        return df
