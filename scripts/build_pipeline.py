import logging
import os
from ml.ingestion import DataIngestor
from ml.cleaning import DataCleaner
from ml.joining import DataJoiner

logging.basicConfig(level=logging.INFO)

def run_phase_2():
    # 1. Ingestion
    ingestor = DataIngestor()
    rec_df, sanc_df, pay_df, dqm = ingestor.run()
    
    # 2. Cleaning
    cleaner = DataCleaner(dqm)
    rec_df = cleaner.clean_recommended(rec_df)
    sanc_df = cleaner.clean_sanctioned(sanc_df)
    pay_df = cleaner.clean_payments(pay_df)
    
    # 3. Joining
    joiner = DataJoiner(dqm)
    joined_df = joiner.run(rec_df, sanc_df, pay_df)
    
    # 4. Feature Engineering
    from ml.feature_engineering import FeatureEngineer
    fe = FeatureEngineer()
    joined_df = fe.run(joined_df, reference_date="2024-09-01")
    
    # 5. Rule Engine
    from ml.rules import RuleEngine
    rule_engine = RuleEngine()
    joined_df, alerts_df = rule_engine.run(joined_df)
    
    # 6. ML Model
    from ml.anomaly_model import AnomalyModel
    ml_model = AnomalyModel()
    joined_df = ml_model.train_and_score(joined_df)
    
    # 7. Risk Scoring and Explanations
    from ml.risk_scoring import RiskScorer, Explainer
    scorer = RiskScorer()
    joined_df = scorer.compute_scores(joined_df)
    
    explainer = Explainer()
    joined_df, alerts_df = explainer.add_explanations(joined_df, alerts_df)
    
    alerts_df.to_parquet("data/processed/alerts.parquet")
    joined_df.to_parquet("data/processed/projects_analytical.parquet")
    
    # Save Report
    dqm.save_report()
    dqm.print_summary()
    
    # 8. Seed Database
    from scripts.seed_db import seed_database
    seed_database()
    
    return joined_df, dqm

if __name__ == "__main__":
    run_phase_2()
