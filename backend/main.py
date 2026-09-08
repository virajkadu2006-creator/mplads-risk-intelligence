from fastapi import FastAPI, Depends, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
import uuid
import io
import csv
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mplads.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create investigation_notes table if not exists
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS investigation_notes (
            note_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            note_text TEXT NOT NULL,
            created_by TEXT DEFAULT 'Auditor',
            created_at TEXT NOT NULL
        )
    """))

app = FastAPI(title="MPLADS Risk Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class NoteCreate(BaseModel):
    note_text: str
    created_by: str = "Auditor"

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    states = [r[0] for r in db.execute(text("SELECT DISTINCT state FROM projects WHERE state IS NOT NULL ORDER BY state")).fetchall()]
    categories = [r[0] for r in db.execute(text("SELECT DISTINCT work_category FROM projects WHERE work_category IS NOT NULL ORDER BY work_category")).fetchall()]
    statuses = [r[0] for r in db.execute(text("SELECT DISTINCT work_status FROM projects WHERE work_status IS NOT NULL ORDER BY work_status")).fetchall()]
    return {
        "states": states,
        "categories": categories,
        "statuses": statuses,
        "risk_levels": ["Critical", "High", "Medium", "Low"]
    }

@app.get("/statistics")
def get_statistics(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT report_json FROM data_quality ORDER BY generated_at DESC LIMIT 1")).fetchone()
    dq = result[0] if result else "{}"
    
    total_works = db.execute(text("SELECT COUNT(*) FROM projects")).scalar()
    sanc_funds = db.execute(text("SELECT SUM(sanction_amount) FROM projects")).scalar()
    spent_funds = db.execute(text("SELECT SUM(amount_spent) FROM projects")).scalar()
    
    risk_counts = db.execute(text("SELECT risk_category, COUNT(*) FROM projects GROUP BY risk_category")).fetchall()
    
    return {
        "kpis": {
            "total_works": total_works,
            "total_sanctioned": sanc_funds,
            "total_spent": spent_funds,
            "risk_counts": {r[0]: r[1] for r in risk_counts}
        },
        "data_quality": dq
    }

@app.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    state: str = Query(None),
    risk_level: str = Query(None),
    category: str = Query(None),
    status: str = Query(None),
    q: str = Query(None),
    sort: str = Query("risk_score"),
    order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=5000)
):
    query = "SELECT * FROM projects WHERE 1=1"
    params = {}
    
    if state:
        query += " AND state = :state"
        params['state'] = state
    if risk_level:
        query += " AND risk_category = :risk_level"
        params['risk_level'] = risk_level
    if category:
        query += " AND work_category = :category"
        params['category'] = category
    if status:
        query += " AND work_status = :status"
        params['status'] = status
    if q:
        query += " AND (work_name LIKE :q OR mp_name LIKE :q OR project_id LIKE :q)"
        params['q'] = f"%{q}%"
        
    # Count total
    count_query = f"SELECT COUNT(*) FROM ({query})"
    total = db.execute(text(count_query), params).scalar()
    
    # Sorting
    valid_sorts = ['risk_score', 'sanction_amount', 'amount_spent', 'delay_days', 'project_id']
    if sort not in valid_sorts:
        sort = 'risk_score'
    order_dir = 'ASC' if order.lower() == 'asc' else 'DESC'
    
    query += f" ORDER BY {sort} {order_dir} LIMIT :limit OFFSET :offset"
    params['limit'] = page_size
    params['offset'] = (page - 1) * page_size
    
    rows = db.execute(text(query), params).fetchall()
    columns = db.execute(text(query), params).keys()
    
    data = [dict(zip(columns, row)) for row in rows]
    
    return {
        "data": data,
        "pagination": {"page": page, "page_size": page_size, "total": total}
    }

@app.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM projects WHERE project_id = :pid"), {"pid": project_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
        
    columns = db.execute(text("SELECT * FROM projects WHERE project_id = :pid"), {"pid": project_id}).keys()
    project_data = dict(zip(columns, row))
    
    # Alerts
    alerts_rows = db.execute(text("SELECT * FROM alerts WHERE project_id = :pid"), {"pid": project_id}).fetchall()
    alerts_cols = db.execute(text("SELECT * FROM alerts WHERE project_id = :pid"), {"pid": project_id}).keys()
    alerts = [dict(zip(alerts_cols, r)) for r in alerts_rows]
    
    # Notes
    notes_rows = db.execute(
        text("SELECT note_id, note_text, created_by, created_at FROM investigation_notes WHERE project_id = :pid ORDER BY created_at DESC"),
        {"pid": project_id}
    ).fetchall()
    notes = [dict(zip(["note_id", "note_text", "created_by", "created_at"], nr)) for nr in notes_rows]
    
    # Similar / Duplicate projects
    dup_group = project_data.get("duplicate_group_id")
    similar_projects = []
    if dup_group:
        similar_rows = db.execute(
            text("SELECT project_id, work_name, risk_score, risk_category FROM projects WHERE duplicate_group_id = :dgroup AND project_id != :pid"),
            {"dgroup": dup_group, "pid": project_id}
        ).fetchall()
        similar_projects = [dict(zip(["project_id", "work_name", "risk_score", "risk_category"], sr)) for sr in similar_rows]

    # Peer comparison (Percentile in same category)
    cat = project_data.get("work_category")
    cost_ratio = project_data.get("cost_overrun_ratio") or 0.0
    delay = project_data.get("delay_days") or 0
    
    peer_comparison = {"category": cat, "percentile_cost": 50, "percentile_delay": 50}
    if cat:
        total_in_cat = db.execute(text("SELECT COUNT(*) FROM projects WHERE work_category = :cat"), {"cat": cat}).scalar()
        if total_in_cat and total_in_cat > 0:
            lower_cost = db.execute(
                text("SELECT COUNT(*) FROM projects WHERE work_category = :cat AND cost_overrun_ratio <= :cr"),
                {"cat": cat, "cr": cost_ratio}
            ).scalar()
            lower_delay = db.execute(
                text("SELECT COUNT(*) FROM projects WHERE work_category = :cat AND delay_days <= :dd"),
                {"cat": cat, "dd": delay}
            ).scalar()
            peer_comparison["percentile_cost"] = round((lower_cost / total_in_cat) * 100)
            peer_comparison["percentile_delay"] = round((lower_delay / total_in_cat) * 100)

    # Provenance
    provenance = {
        "source_files": ["recommended_works.csv", "sanctioned_works.csv", "payments.csv"],
        "model_version": project_data.get("model_version", "isolation_forest_v1"),
        "rule_version": "rules_v1",
        "features_used": ["sanction_amount", "amount_spent", "cost_overrun_ratio", "delay_days", "underutilization_ratio", "duplicate_similarity_max", "max_vendor_share"]
    }

    return {
        "data": {
            **project_data,
            "alerts": alerts,
            "notes": notes,
            "similar_projects": similar_projects,
            "peer_comparison": peer_comparison,
            "provenance": provenance
        }
    }

@app.post("/projects/{project_id}/notes")
def add_investigation_note(project_id: str, note: NoteCreate, db: Session = Depends(get_db)):
    # Check if project exists
    p = db.execute(text("SELECT project_id FROM projects WHERE project_id = :pid"), {"pid": project_id}).fetchone()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
        
    note_id = str(uuid.uuid4())
    now_str = datetime.utcnow().isoformat() + "Z"
    db.execute(
        text("INSERT INTO investigation_notes (note_id, project_id, note_text, created_by, created_at) VALUES (:nid, :pid, :text, :by, :at)"),
        {"nid": note_id, "pid": project_id, "text": note.note_text, "by": note.created_by, "at": now_str}
    )
    db.commit()
    return {
        "status": "success",
        "note": {
            "note_id": note_id,
            "project_id": project_id,
            "note_text": note.note_text,
            "created_by": note.created_by,
            "created_at": now_str
        }
    }

@app.get("/states")
def get_states_summary(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT 
            state,
            COUNT(*) as total_works,
            COALESCE(SUM(sanction_amount), 0) as total_sanctioned,
            COALESCE(SUM(amount_spent), 0) as total_spent,
            COALESCE(SUM(CASE WHEN risk_category = 'Critical' THEN 1 ELSE 0 END), 0) as critical_count,
            COALESCE(SUM(CASE WHEN risk_category = 'High' THEN 1 ELSE 0 END), 0) as high_count,
            COALESCE(SUM(CASE WHEN risk_category = 'Medium' THEN 1 ELSE 0 END), 0) as medium_count,
            COALESCE(SUM(CASE WHEN risk_category = 'Low' THEN 1 ELSE 0 END), 0) as low_count,
            COALESCE(AVG(risk_score), 0) as avg_risk_score
        FROM projects
        WHERE state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY (critical_count + high_count) DESC
    """)).fetchall()
    cols = ["state", "total_works", "total_sanctioned", "total_spent", "critical_count", "high_count", "medium_count", "low_count", "avg_risk_score"]
    return {"data": [dict(zip(cols, r)) for r in rows]}

@app.get("/anomalies")
def list_anomalies(
    db: Session = Depends(get_db),
    alert_type: str = Query(None),
    severity: str = Query(None),
    limit: int = Query(50, le=500)
):
    query = "SELECT * FROM alerts WHERE 1=1"
    params = {}
    if alert_type:
        query += " AND alert_type = :alert_type"
        params["alert_type"] = alert_type
    if severity:
        query += " AND severity = :severity"
        params["severity"] = severity
    query += " ORDER BY triggered_at DESC LIMIT :limit"
    params["limit"] = limit
    
    rows = db.execute(text(query), params).fetchall()
    cols = db.execute(text(query), params).keys()
    return {"data": [dict(zip(cols, r)) for r in rows]}

@app.get("/export/csv")
def export_projects_csv(
    db: Session = Depends(get_db),
    state: str = Query(None),
    risk_level: str = Query(None)
):
    query = "SELECT project_id, mp_name, state, district, constituency, work_name, work_category, sanction_amount, amount_spent, delay_days, ml_risk_score, risk_score, risk_category FROM projects WHERE 1=1"
    params = {}
    if state:
        query += " AND state = :state"
        params["state"] = state
    if risk_level:
        query += " AND risk_category = :risk_level"
        params["risk_level"] = risk_level
    query += " ORDER BY risk_score DESC"
    
    rows = db.execute(text(query), params).fetchall()
    cols = ["project_id", "mp_name", "state", "district", "constituency", "work_name", "work_category", "sanction_amount", "amount_spent", "delay_days", "ml_risk_score", "risk_score", "risk_category"]
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(cols)
    for r in rows:
        writer.writerow(list(r))
        
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mplads_risk_projects.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
