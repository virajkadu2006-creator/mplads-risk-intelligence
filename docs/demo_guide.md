# MPLADS Risk Intelligence System — Live Demo & Presentation Script
### Smart India Hackathon — Problem Statement 26102

**Target Demo Duration:** 3 to 5 minutes  
**Application URL:** [http://localhost:8501](http://localhost:8501)  
**API Backend Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)  

---

## 🎯 The Core Narrative Spine
Lead with this exact framing:
> *"MPLADS handles thousands of works across every constituency in India. Manual review of every single voucher and sanction is physically impossible. Our system acts as an automated, explainable intelligence layer that scans 100% of works, applies multi-signal rules plus unsupervised machine learning, and produces a prioritized, evidence-backed audit shortlist for officers."*

---

## ⏱️ Step-by-Step 4-Minute Presentation Walkthrough

### 1. Minute 0:00 – 0:45 | Screen 1: Executive Overview
- **Action:** Open `http://localhost:8501` on the default **Overview** tab.
- **Narrate:**
  - *"Here is the macro overview across 1,001 developmental works representing over ₹940 Crore in sanctioned funds."*
  - *"Notice the **Data Quality Score**: Our automated ingestion pipeline validates schemas, checks for negative or unparseable amounts, and tracks join coverage before any score is calculated."*
  - *"Look at the risk distribution pie chart: Rather than overwhelming auditors, the system isolates the 85 works categorized as High or Critical Risk for prioritized inspection."*

### 2. Minute 0:45 – 1:30 | Screen 2: Risk Monitor
- **Action:** Click **Risk Monitor** in the left sidebar. Set **Filter by Severity** to `Critical` or `High`.
- **Narrate:**
  - *"The Risk Monitor gives district and central officers a globally ranked triage table. Every project is sorted by our composite 0–100 Risk Score."*
  - *"Auditors can instantly filter by State, Work Category, or search by MP name or Work ID."*
  - *"Notice how works with severe cost overruns (e.g. 150%+ spend) or extreme delays (>400 days) naturally surface to the top."*
- **Action:** Pick a top project (e.g., one with Score > 80) from the dropdown and click **"Open Investigation Dossier"**.

### 3. Minute 1:30 – 3:00 | Screen 3: Project Investigation Dossier (The "Wow" Screen)
- **Action:** Walk down Screen 3:
  1. **Identity & 5-Second Rule:**
     - Point at the large **Risk Score (e.g., 86/100) Badge**: *"Within 5 seconds, an auditor sees the exact risk tier without deciphering confusing spreadsheets."*
  2. **Plain-Language Alert Box:**
     - Read the generated explanation: *"Notice the explanation: Cost exceeded sanction by 45% (₹X spent vs ₹Y sanctioned) and project is delayed by 420 days."*
     - Emphasize: *"No black box. Every alert is written in clear, objective language that respects responsible AI guidelines—it presents evidence without making premature accusations of fraud."*
  3. **Financial & Progress Panels:**
     - Point at the progress bar: *"Visual comparison of sanction vs. recorded expenditure."*
  4. **Peer Benchmarking:**
     - Point at the percentile metric: *"This work's overrun is higher than 95% of other Road projects in our database."*
  5. **Unsupervised ML Panel:**
     - *"Beyond static rules, our trained **Isolation Forest** model independently analyzed 7 multivariate features and flagged this as a statistical outlier with an anomaly score of 82/100."*
  6. **Duplicate / Overlapping Works Panel:**
     - If the project has duplicate candidates: *"Our fuzzy matching engine caught a potential duplicate work in the same district and category under Group DUP_1."*
  7. **Investigation Notes & Case Log:**
     - Type a quick note (e.g., *"Site inspection requested on 08/09"*), click **Save Note**.
     - *"Auditors can maintain an auditable case log stored in the SQLite database for field compliance."*
  8. **Audit Provenance Expander:**
     - Expand to show exact source tables, feature lists, and rule/model versions (`isolation_forest_v1`, `rules_v1`).

### 4. Minute 3:00 – 3:30 | Screen 4: Geographic Analysis & Screen 5: ML Insights
- **Action:** Click **Geo Analysis**:
  - *"Central authorities can see geographic risk concentration by state and district to allocate audit task forces where discrepancies cluster."*
- **Action:** Click **ML Insights**:
  - *"Here is the 2D cluster visualization: cost overrun ratio vs timeline delay, colored by risk category, demonstrating clear statistical separation between normal projects and anomalous outliers."*

### 5. Minute 3:30 – 4:00 | Closing & Judging Alignment
- **Conclude:**
  - *"To summarize: **Real data structures + Deterministic rules + Isolation Forest ML + 100% Explainable 0–100 scoring + Live interactive dashboard**."*
  - *"Our system does not replace human judgment—it empowers officers to focus their limited audit capacity on the 5% of projects that require urgent attention."*
  - *"Thank you! We're ready for your questions."*

---

## 🛡️ Quick Answers for Tough Judge Questions

| Judge Question | Winning Answer |
|---|---|
| **Why not use supervised Deep Learning or XGBoost?** | *"There is no ground-truth labeled fraud dataset for MPLADS works. Supervised models would hallucinate or overfit on synthetic labels. Unsupervised Isolation Forest detects real statistical outliers without bias."* |
| **Does your system accuse MPs of corruption?** | *"Never. As codified in Part 6.3 of our spec, our system generates analytical risk signals requiring human audit. No alert template ever uses words like fraud, corrupt, or guilty."* |
| **How does it scale?** | *"The data pipeline is layered (Raw → Cleaned → Analytical → Database). We use SQLite with SQLAlchemy ORM—switching to PostgreSQL in production is a single connection-string configuration change."* |
| **Are the thresholds hardcoded?** | *"No, 100% of thresholds live in `config/thresholds.yaml` with explicit source tags ([VERIFIED], [CONFIGURABLE]) so government guidelines can be adjusted dynamically."* |
