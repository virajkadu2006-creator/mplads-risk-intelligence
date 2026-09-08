import pandas as pd
import numpy as np
import logging
from ml.data_quality import DataQualityMonitor

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, dqm: DataQualityMonitor):
        self.dqm = dqm

    def clean_amounts(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        for col in columns:
            if col in df.columns:
                # Remove currency symbols and commas if it's string
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(r'[₹$,]', '', regex=True)
                    # Convert lakh/crore
                    df[col] = df[col].apply(self._parse_indian_currency)
                
                # Convert to numeric
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Flag negatives (set to NaN to exclude from math)
                neg_mask = df[col] < 0
                if neg_mask.any():
                    self.dqm.record_rejection(f"cleaned_negative_{col}", neg_mask.sum())
                    df.loc[neg_mask, col] = np.nan
        return df

    def _parse_indian_currency(self, val_str: str) -> float:
        val_str = str(val_str).lower().strip()
        if 'lakh' in val_str:
            num = val_str.replace('lakh', '').strip()
            try: return float(num) * 100000
            except: return np.nan
        elif 'crore' in val_str:
            num = val_str.replace('crore', '').strip()
            try: return float(num) * 10000000
            except: return np.nan
        elif val_str == 'nan':
            return np.nan
        else:
            try: return float(val_str)
            except: return np.nan

    def clean_dates(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        for col in columns:
            if col in df.columns:
                # Coerce errors to NaT
                df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
                # Flag impossible dates (e.g. before 1993)
                impossible_mask = df[col].dt.year < 1993
                if impossible_mask.any():
                    self.dqm.record_rejection(f"impossible_date_{col}", impossible_mask.sum())
                    df.loc[impossible_mask, col] = pd.NaT
        return df

    def normalize_text(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        for col in columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.title()
                df[col] = df[col].replace('Nan', np.nan)
        return df

    def clean_recommended(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.clean_amounts(df, ['recommended_amount'])
        df = self.clean_dates(df, ['date_recommended'])
        df = self.normalize_text(df, ['mp_name', 'state', 'constituency', 'work_category', 'implementing_agency'])
        if 'work_name' in df.columns:
            df['work_name_normalized'] = df['work_name'].astype(str).str.lower().str.strip().str.replace(r'[^\w\s]', '', regex=True)
            # Remove stopwords
            stopwords = ["construction", "of", "repair", "work", "at", "in"]
            df['work_name_normalized'] = df['work_name_normalized'].apply(
                lambda x: ' '.join([w for w in x.split() if w not in stopwords])
            )
        return df

    def clean_sanctioned(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.clean_amounts(df, ['sanction_amount'])
        df = self.clean_dates(df, ['sanction_date'])
        df = self.normalize_text(df, ['work_status', 'implementing_agency', 'district'])
        return df

    def clean_payments(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.clean_amounts(df, ['amount_spent'])
        df = self.clean_dates(df, ['payment_date'])
        df = self.normalize_text(df, ['payment_status', 'vendor_name'])
        return df
