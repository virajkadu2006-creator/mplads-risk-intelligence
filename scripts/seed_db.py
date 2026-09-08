import pandas as pd
from sqlalchemy import create_engine
import os
import json

def seed_database(db_path="sqlite:///mplads.db"):
    engine = create_engine(db_path)
    
    projects_df = pd.read_parquet("data/processed/projects_analytical.parquet")
    alerts_df = pd.read_parquet("data/processed/alerts.parquet")
    
    # Need to convert list/dict columns to strings or JSON strings to store in sqlite
    # But currently we don't have list/dict columns in projects_df directly, except maybe some dates that should be str
    projects_df.to_sql("projects", con=engine, if_exists="replace", index=False)
    alerts_df.to_sql("alerts", con=engine, if_exists="replace", index=False)
    
    # Store model_metadata if present
    if os.path.exists("ml/models/model_metadata.json"):
        with open("ml/models/model_metadata.json", "r") as f:
            metadata = json.load(f)
            metadata['feature_list'] = json.dumps(metadata['feature_list'])
            metadata['normalization_bounds'] = json.dumps(metadata['normalization_bounds'])
            
            meta_df = pd.DataFrame([metadata])
            meta_df.to_sql("model_metadata", con=engine, if_exists="replace", index=False)
            
    if os.path.exists("data/processed/data_quality_report.json"):
        with open("data/processed/data_quality_report.json", "r") as f:
            dqm = json.load(f)
            dq_df = pd.DataFrame([{
                "run_id": dqm["run_id"],
                "generated_at": dqm["generated_at"],
                "report_json": json.dumps(dqm)
            }])
            dq_df.to_sql("data_quality", con=engine, if_exists="replace", index=False)
            
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_database()
