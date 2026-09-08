import pandas as pd
import numpy as np
import logging
import os
import uuid
from ml.data_quality import DataQualityMonitor

logger = logging.getLogger(__name__)

class DataIngestor:
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.run_id = str(uuid.uuid4())
        self.dqm = DataQualityMonitor(self.run_id)
        os.makedirs(self.processed_dir, exist_ok=True)

    def load_csv(self, filename: str) -> pd.DataFrame:
        filepath = os.path.join(self.raw_dir, filename)
        if not os.path.exists(filepath):
            logger.error(f"Missing required file: {filepath}")
            raise FileNotFoundError(f"Missing required file: {filepath}")
        
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {filename}. Falling back to latin-1.")
            df = pd.read_csv(filepath, encoding='latin-1')
            
        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def validate_and_filter(self, df: pd.DataFrame, file_type: str, required_cols: list) -> pd.DataFrame:
        initial_count = len(df)
        self.dqm.record_ingestion(file_type, initial_count)
        
        if df.empty:
            logger.warning(f"File {file_type} is empty.")
            return df
            
        # Check missing required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"File {file_type} missing required columns: {missing_cols}")

        # Missing ID
        id_col = "unique_work_number"
        missing_id_mask = df[id_col].isnull() | (df[id_col].astype(str).str.strip() == "")
        if missing_id_mask.any():
            missing_count = missing_id_mask.sum()
            self.dqm.record_rejection("missing_id", missing_count)
            # Log rejected rows
            rejected = df[missing_id_mask]
            rejected.to_parquet(os.path.join(self.processed_dir, f"{file_type}_rejected_missing_id.parquet"))
            df = df[~missing_id_mask]
            
        # Amounts non-negativity
        amount_cols = [col for col in df.columns if "amount" in col.lower()]
        for col in amount_cols:
            # Attempt to convert to numeric, coerce errors to NaN
            df_col_numeric = pd.to_numeric(df[col], errors='coerce')
            negative_mask = df_col_numeric < 0
            if negative_mask.any():
                neg_count = negative_mask.sum()
                self.dqm.record_rejection(f"negative_{col}", neg_count)
                # We don't drop negative rows per spec, just flag them. The cleaning step will handle them or set them to NaN.

        # Duplicates within same file
        duplicates_mask = df.duplicated(subset=[id_col], keep='last')
        if duplicates_mask.any():
            dup_count = duplicates_mask.sum()
            self.dqm.record_rejection(f"duplicate_{id_col}", dup_count)
            rejected_dups = df[duplicates_mask]
            rejected_dups.to_parquet(os.path.join(self.processed_dir, f"{file_type}_discarded_duplicates.parquet"))
            df = df[~duplicates_mask]

        return df

    def run(self):
        logger.info("Starting ingestion phase...")
        rec_df = self.load_csv("recommended_works.csv")
        sanc_df = self.load_csv("sanctioned_works.csv")
        pay_df = self.load_csv("payments.csv")
        
        rec_df = self.validate_and_filter(rec_df, "recommended", ["unique_work_number"])
        sanc_df = self.validate_and_filter(sanc_df, "sanctioned", ["unique_work_number", "sanction_amount"])
        pay_df = self.validate_and_filter(pay_df, "payments", ["unique_work_number", "amount_spent"])
        
        # Save raw-validated state
        rec_df.to_parquet(os.path.join(self.processed_dir, "recommended_validated.parquet"))
        sanc_df.to_parquet(os.path.join(self.processed_dir, "sanctioned_validated.parquet"))
        pay_df.to_parquet(os.path.join(self.processed_dir, "payments_validated.parquet"))
        
        logger.info("Ingestion complete.")
        return rec_df, sanc_df, pay_df, self.dqm
