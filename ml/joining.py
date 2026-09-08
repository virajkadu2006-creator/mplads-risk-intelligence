import pandas as pd
import numpy as np
import logging
import os
from ml.data_quality import DataQualityMonitor

logger = logging.getLogger(__name__)

class DataJoiner:
    def __init__(self, dqm: DataQualityMonitor, processed_dir="data/processed"):
        self.dqm = dqm
        self.processed_dir = processed_dir

    def run(self, rec_df: pd.DataFrame, sanc_df: pd.DataFrame, pay_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting joining phase...")
        
        # Aggregate payments if itemized
        if 'amount_spent' in pay_df.columns:
            pay_agg = pay_df.groupby('unique_work_number').agg(
                amount_spent=('amount_spent', 'sum'),
                num_payments=('amount_spent', 'count'),
                last_payment_date=('payment_date', 'max')
            ).reset_index()
            
            # Vendor concentration
            if 'vendor_name' in pay_df.columns:
                # Find max vendor share
                def max_share(group):
                    total = group['amount_spent'].sum()
                    if total == 0: return 0
                    max_vendor_total = group.groupby('vendor_name')['amount_spent'].sum().max()
                    return max_vendor_total / total
                
                vendor_shares = pay_df.groupby('unique_work_number').apply(max_share).reset_index(name='max_vendor_share')
                pay_agg = pd.merge(pay_agg, vendor_shares, on='unique_work_number', how='left')
        else:
            pay_agg = pay_df.copy()
            pay_agg['num_payments'] = np.nan

        # Merge rec + sanc
        joined_df = pd.merge(rec_df, sanc_df, on='unique_work_number', how='left', suffixes=('', '_sanc'))
        
        # Resolve conflicting columns (prefer sanc over rec)
        if 'implementing_agency_sanc' in joined_df.columns:
            joined_df['implementing_agency'] = joined_df['implementing_agency_sanc'].combine_first(joined_df['implementing_agency'])
            joined_df.drop(columns=['implementing_agency_sanc'], inplace=True)
            
        # Merge payments
        joined_df = pd.merge(joined_df, pay_agg, on='unique_work_number', how='left')
        
        # Log orphans
        # Records in sanc but not in rec
        sanc_orphans = sanc_df[~sanc_df['unique_work_number'].isin(rec_df['unique_work_number'])]
        if not sanc_orphans.empty:
            self.dqm.record_unmatched(len(sanc_orphans))
            sanc_orphans.to_parquet(os.path.join(self.processed_dir, "sanc_orphans.parquet"))
            # We add them to joined_df using outer join, or keep as orphans?
            # Spec says "recommended LEFT JOIN sanctioned LEFT JOIN payments". We'll just stick to left joins and log orphans.
            
        pay_orphans = pay_df[~pay_df['unique_work_number'].isin(joined_df['unique_work_number'])]
        if not pay_orphans.empty:
            self.dqm.record_unmatched(len(pay_orphans))
            pay_orphans.to_parquet(os.path.join(self.processed_dir, "pay_orphans.parquet"))

        self.dqm.calculate_coverage(len(joined_df))
        self.dqm.calculate_nullness(joined_df)
        
        # Save analytical table
        joined_df['project_id'] = joined_df['unique_work_number']
        joined_df.to_parquet(os.path.join(self.processed_dir, "projects_analytical_base.parquet"))
        
        logger.info(f"Joining complete. Final dataset size: {len(joined_df)}")
        return joined_df
