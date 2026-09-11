import os
import threading
import time
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Auto-launcher for FastAPI backend if not currently reachable (e.g. Streamlit Cloud)
def ensure_backend_running():
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            return
    except Exception:
        pass
    
    def run_server():
        try:
            import uvicorn
            import sys
            # Ensure repository root is in python path
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if root_dir not in sys.path:
                sys.path.insert(0, root_dir)
            from backend.main import app as fastapi_app
            uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")
        except Exception as err:
            print("Auto-backend launch warning:", err)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2)

ensure_backend_running()


st.set_page_config(
    page_title="MPLADS Risk Intelligence System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navigation state
if "page" not in st.session_state:
    st.session_state.page = "Overview"

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark 🌙"

# Sidebar controls
st.sidebar.markdown("### 🏛️ MPLADS Risk Intelligence")
st.sidebar.caption("SIH PS-26102 | Decision-Support System")

pages = ["Overview", "Risk Monitor", "Project Investigation", "Geo Analysis", "ML Insights"]
current_page = st.sidebar.radio("Navigation", pages, index=pages.index(st.session_state.page) if st.session_state.page in pages else 0)
st.session_state.page = current_page

st.sidebar.markdown("---")
theme = st.sidebar.radio("🎨 Theme Mode", ["Dark 🌙", "Light ☀️"], index=0 if "Dark" in st.session_state.theme_mode else 1)
st.session_state.theme_mode = theme
is_dark = "Dark" in theme

# Theme variables
bg_color = "#0f172a" if is_dark else "#f8fafc"
card_bg = "#1e293b" if is_dark else "#ffffff"
card_border = "#334155" if is_dark else "#e2e8f0"
text_color = "#f8fafc" if is_dark else "#1e293b"
muted_text = "#94a3b8" if is_dark else "#64748b"
disclaimer_border = "#334155" if is_dark else "#cbd5e1"
plotly_template = "plotly_dark" if is_dark else "plotly_white"

# Dynamic CSS Injection
st.markdown(f"""
<style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .main-header {{
        font-size: 26px;
        font-weight: 700;
        color: {text_color};
        margin-bottom: 20px;
    }}
    .metric-card {{
        background: {card_bg};
        padding: 18px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        border: 1px solid {card_border};
        color: {text_color};
    }}
    .card-label {{
        font-size: 14px;
        color: {muted_text};
    }}
    .card-value {{
        font-size: 42px;
        font-weight: 800;
        color: {text_color};
    }}
    .badge-critical {{
        background-color: {"rgba(185, 28, 28, 0.25)" if is_dark else "#fee2e2"};
        color: {"#fca5a5" if is_dark else "#991b1b"};
        border: 1px solid {"#ef4444" if is_dark else "#f87171"};
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }}
    .badge-high {{
        background-color: {"rgba(234, 88, 12, 0.25)" if is_dark else "#ffedd5"};
        color: {"#fdba74" if is_dark else "#9a3412"};
        border: 1px solid {"#f97316" if is_dark else "#fb923c"};
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }}
    .badge-medium {{
        background-color: {"rgba(234, 179, 8, 0.25)" if is_dark else "#fef9c3"};
        color: {"#fde047" if is_dark else "#854d0e"};
        border: 1px solid {"#eab308" if is_dark else "#facc15"};
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }}
    .badge-low {{
        background-color: {"rgba(22, 163, 74, 0.25)" if is_dark else "#dcfce7"};
        color: {"#86efac" if is_dark else "#166534"};
        border: 1px solid {"#22c55e" if is_dark else "#4ade80"};
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 600;
    }}
    .disclaimer {{
        font-size: 12px;
        color: {muted_text};
        border-top: 1px solid {disclaimer_border};
        padding-top: 12px;
        margin-top: 30px;
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=15)
def fetch_api(endpoint, params=None):
    try:
        response = requests.get(f"{API_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

def post_api(endpoint, payload):
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10)
        response.raise_for_status()
        st.cache_data.clear()
        return response.json()
    except Exception as e:
        st.error(f"Action failed: {e}")
        return None

# -------------------------------------------------------------
# SCREEN 1: OVERVIEW
# -------------------------------------------------------------
if st.session_state.page == "Overview":
    st.markdown("<div class='main-header'>📊 Executive Overview</div>", unsafe_allow_html=True)
    
    stats = fetch_api("/statistics")
    if stats:
        kpis = stats["kpis"]
        dq_raw = stats.get("data_quality", "{}")
        dq = json.loads(dq_raw) if isinstance(dq_raw, str) else dq_raw
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Works Ingested", f"{kpis['total_works']:,}")
        c2.metric("Total Sanctioned", f"₹{kpis['total_sanctioned']/1e7:.2f} Cr" if kpis['total_sanctioned'] else "₹0")
        c3.metric("Total Expenditure", f"₹{kpis['total_spent']/1e7:.2f} Cr" if kpis['total_spent'] else "₹0")
        
        rc = kpis.get("risk_counts", {})
        high_crit = rc.get("High", 0) + rc.get("Critical", 0)
        c4.metric("High/Critical Risk", f"{high_crit}", delta=f"{rc.get('Critical', 0)} Critical", delta_color="inverse")
        raw_cov = float(dq.get('join_coverage_pct', 0))
        capped_cov = min(100.0, raw_cov)
        cov_str = f"{capped_cov:.1f}%" if capped_cov % 1 != 0 else f"{int(capped_cov)}%"
        c5.metric("Data Quality Score", f"{cov_str} Valid")
        
        st.markdown("---")
        col_pie, col_bar = st.columns([1, 1])
        
        with col_pie:
            st.subheader("Risk Severity Breakdown")
            df_risk = pd.DataFrame(list(rc.items()), columns=["Category", "Count"])
            fig_pie = px.pie(
                df_risk, names="Category", values="Count", color="Category",
                color_discrete_map={"Critical": "#b91c1c", "High": "#ea580c", "Medium": "#eab308", "Low": "#16a34a"},
                hole=0.4
            )
            fig_pie.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_pie, width='stretch')
            
        with col_bar:
            st.subheader("Funds Overview (Sanctioned vs Spent)")
            funds_df = pd.DataFrame({
                "Type": ["Sanctioned", "Spent"],
                "Amount (₹ Cr)": [kpis['total_sanctioned']/1e7, kpis['total_spent']/1e7]
            })
            fig_bar = px.bar(funds_df, x="Type", y="Amount (₹ Cr)", color="Type", color_discrete_sequence=["#3b82f6", "#0d9488"])
            fig_bar.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, width='stretch')
            
        st.info("💡 **Auditor Workflow:** Go to **Risk Monitor** to inspect ranked candidate projects, or click **Project Investigation** to view evidence dossiers.")

# -------------------------------------------------------------
# SCREEN 2: RISK MONITOR
# -------------------------------------------------------------
elif st.session_state.page == "Risk Monitor":
    st.markdown("<div class='main-header'>🔍 Risk Monitor (Global Ranked Projects)</div>", unsafe_allow_html=True)
    
    with st.expander("ℹ️ How is the Composite Risk Score Calculated? (Click to expand)"):
        st.markdown("""
        **The Composite Risk Score (0 – 100)** is calculated using 5 weighted analytical risk indicators:
        
        | Risk Component | Max Weight | Calculation Logic & Description |
        | :--- | :--- | :--- |
        | **💰 Cost Overrun** | **25 pts** | Based on expenditure vs sanction ratio (`amount_spent / sanction_amount`). Overruns above 1.0 scale up to 25 pts for a 2.0x overrun. |
        | **⏱️ Timeline Delay** | **25 pts** | Based on project duration exceeding the 1-year (365-day) norm. Delays up to 730 days scale linearly to 25 pts. |
        | **🤖 ML Anomaly Score** | **25 pts** | Unsupervised Isolation Forest model score [0 to 25 pts] detecting multivariate outliers across 7 scaled features. |
        | **⚖️ Compliance & Trust** | **25 pts** | Triggered if MP annual trust/society aggregate cap (>₹1 Crore) is breached or exact duplicate works exist. |
        | **📉 Under-Utilization** | **+15 pts** | Applied as an added penalty if project age > 180 days with < 10% fund utilization. |
        
        *Total score is clipped to a maximum of 100 points. Risk levels are categorized into:*
        - 🟢 **Low Risk**: 0 – 24 pts
        - 🟡 **Medium Risk**: 25 – 49 pts
        - 🟠 **High Risk**: 50 – 74 pts
        - 🔴 **Critical Risk**: 75 – 100 pts
        """)

    filters_data = fetch_api("/filters") or {"states": [], "categories": [], "risk_levels": ["Critical", "High", "Medium", "Low"]}
    
    fc1, fc2, fc3, fc4 = st.columns(4)
    risk_level = fc1.selectbox("Filter by Severity", ["All"] + filters_data.get("risk_levels", []))
    state = fc2.selectbox("Filter by State", ["All"] + filters_data.get("states", []))
    category = fc3.selectbox("Filter by Category", ["All"] + filters_data.get("categories", []))
    search_q = fc4.text_input("Search (ID, MP, Work Name)")
    
    params = {"page_size": 200, "sort": "risk_score", "order": "desc"}
    if risk_level != "All": params["risk_level"] = risk_level
    if state != "All": params["state"] = state
    if category != "All": params["category"] = category
    if search_q: params["q"] = search_q
    
    projects_res = fetch_api("/projects", params)
    
    if projects_res and projects_res.get("data"):
        data = projects_res["data"]
        df = pd.DataFrame(data)
        
        # Derive explicit MP Number column (e.g., MP #19 from MP_19)
        df["mp_number"] = df["mp_name"].apply(lambda name: f"MP #{str(name).split('_')[-1]}" if name and '_' in str(name) else (f"MP #{name}" if name else "N/A"))
        
        c_head1, c_head2 = st.columns([3, 1])
        c_head1.caption(f"Showing {len(df)} matching projects (sorted by Risk Score desc)")
        
        # CSV Export Button
        csv_data = df.to_csv(index=False)
        c_head2.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="mplads_risk_monitor.csv",
            mime="text/csv"
        )
        
        display_df = df[[
            "project_id", "risk_score", "risk_category", "mp_number", "mp_name", 
            "state", "district", "work_name", "sanction_amount", "amount_spent", "delay_days"
        ]].copy()
        
        display_df.rename(columns={
            "project_id": "Work ID",
            "risk_score": "Score",
            "risk_category": "Risk Level",
            "mp_number": "MP Number",
            "mp_name": "MP Name",
            "state": "State",
            "district": "District",
            "work_name": "Project Name",
            "sanction_amount": "Sanction (₹)",
            "amount_spent": "Spent (₹)",
            "delay_days": "Delay (Days)"
        }, inplace=True)
        
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        st.markdown("### 🔎 Project Deep-Dive")
        col_sel, col_btn = st.columns([3, 1])
        options = [f"{r['project_id']} — {r['work_name']} (Score: {r['risk_score']})" for _, r in df.iterrows()]
        selected_option = col_sel.selectbox("Select project to inspect:", options)
        selected_pid = selected_option.split(" — ")[0]
        
        if col_btn.button("Open Investigation Dossier", type="primary"):
            st.session_state.selected_project = selected_pid
            st.session_state.page = "Project Investigation"
            st.rerun()
    else:
        st.warning("No projects matched the selected filter criteria.")

# -------------------------------------------------------------
# SCREEN 3: PROJECT INVESTIGATION
# -------------------------------------------------------------
elif st.session_state.page == "Project Investigation":
    st.markdown("<div class='main-header'>📁 Project Investigation Dossier</div>", unsafe_allow_html=True)
    
    # Load all project IDs for convenient switching directly on this screen
    all_proj_res = fetch_api("/projects", {"page_size": 200, "sort": "risk_score", "order": "desc"})
    all_projects = all_proj_res.get("data", []) if all_proj_res else []
    
    if all_projects:
        project_ids = [p["project_id"] for p in all_projects]
        id_to_label = {p["project_id"]: f"{p['project_id']} — {p['work_name']} [Score: {p['risk_score']}, {p['risk_category']}]" for p in all_projects}
        
        # If no project selected yet, default to highest risk
        if "selected_project" not in st.session_state or st.session_state.selected_project not in id_to_label:
            st.session_state.selected_project = project_ids[0]
            
        current_idx = project_ids.index(st.session_state.selected_project)
        selected_label = st.selectbox("Switch Project Dossier:", [id_to_label[pid] for pid in project_ids], index=current_idx)
        st.session_state.selected_project = selected_label.split(" — ")[0]
        selected_id = st.session_state.selected_project
    else:
        selected_id = st.session_state.get("selected_project", "W-1000")

    proj_res = fetch_api(f"/projects/{selected_id}")
    if proj_res and proj_res.get("data"):
        p = proj_res["data"]
        
        # Identity Header
        c_meta1, c_meta2 = st.columns([3, 1])
        with c_meta1:
            st.subheader(f"📌 {p.get('work_name')}")
            st.markdown(f"**Work ID:** `{p.get('project_id')}` | **Category:** `{p.get('work_category')}` | **Status:** `{p.get('work_status')}`")
            st.markdown(f"**Hon'ble MP:** {p.get('mp_name')} | **Constituency:** {p.get('constituency')} | **Location:** {p.get('district')}, {p.get('state')}")
            st.markdown(f"**Implementing Agency:** {p.get('implementing_agency')}")
        with c_meta2:
            score = p.get('risk_score', 0)
            cat = p.get('risk_category', 'Low')
            color_class = "badge-critical" if cat == "Critical" else "badge-high" if cat == "High" else "badge-medium" if cat == "Medium" else "badge-low"
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <div class='card-label'>Composite Risk Score</div>
                <div class='card-value'>{score}<span style='font-size: 20px; color:{muted_text};'>/100</span></div>
                <span class='{color_class}'>{cat.upper()} RISK</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Alerts Box
        st.markdown("#### 🚨 Triggered Anomaly Signals & Objective Review Reasons")
        alerts = p.get("alerts", [])
        if alerts:
            for a in alerts:
                sev = a.get("severity", "Info")
                badge = "🔴" if sev == "Critical" else "🟠" if sev == "High" else "🟡"
                st.warning(f"{badge} **[{a.get('alert_type')}]** {a.get('reason_text')}")
        else:
            st.success("No active threshold anomalies detected for this project.")
            
        st.markdown("---")
        
        # Financial & Timeline Panels
        col_fin, col_time = st.columns(2)
        with col_fin:
            st.markdown("#### 💰 Financial Panel")
            sanc = p.get("sanction_amount") or 0.0
            spent = p.get("amount_spent") or 0.0
            overrun = spent - sanc if spent > sanc else 0.0
            ratio = spent / sanc if sanc > 0 else 0.0
            
            st.write(f"- **Sanctioned Amount:** ₹{sanc:,.2f}")
            st.write(f"- **Recorded Expenditure:** ₹{spent:,.2f}")
            if overrun > 0:
                st.write(f"- **Overrun:** :red[+₹{overrun:,.2f} ({ratio*100 - 100:.1f}% over)]")
            else:
                st.write(f"- **Unspent Balance:** ₹{sanc - spent:,.2f}")
                
            st.progress(min(ratio, 1.0))
            st.caption(f"Expenditure to Sanction Ratio: {ratio*100:.1f}%")

        with col_time:
            st.markdown("#### ⏱️ Timeline & Progress Panel")
            st.write(f"- **Recommended Date:** {p.get('date_recommended') or 'N/A'}")
            st.write(f"- **Sanction Date:** {p.get('sanction_date') or 'N/A'}")
            st.write(f"- **Project Age / Duration:** {p.get('delay_days') or 0} days")
            st.write(f"- **1-Year Norm Exceeded:** {'Yes (>365 days)' if p.get('delay_days', 0) > 365 else 'No (within norm)'}")
            
        st.markdown("---")
        
        # Peer Comparison & ML Insights
        col_peer, col_ml = st.columns(2)
        with col_peer:
            st.markdown("#### 👥 Peer Group Benchmarking")
            peer = p.get("peer_comparison", {})
            st.write(f"- **Category:** `{peer.get('category')}`")
            cost_pct = peer.get("percentile_cost", 50)
            delay_pct = peer.get("percentile_delay", 50)
            st.metric("Cost Overrun Percentile", f"{cost_pct}th percentile", help="Percentile vs other projects in the same category")
            st.caption(f"Cost ratio is higher than **{cost_pct}%** of works in {peer.get('category')}.")
            st.metric("Timeline Delay Percentile", f"{delay_pct}th percentile")
            st.caption(f"Project duration is longer than **{delay_pct}%** of works in {peer.get('category')}.")
            
        with col_ml:
            st.markdown("#### 🤖 Unsupervised ML (Isolation Forest)")
            ml_score = p.get("ml_risk_score") or 0.0
            st.metric("ML Anomaly Score", f"{ml_score:.1f}/100", help="Continuous score generated by Isolation Forest across 7 scaled features")
            st.write(f"- **Model:** `{p.get('model_version', 'isolation_forest_v1')}`")
            st.write(f"- **Trees:** 200 | **Contamination assumption:** 5% baseline")
            st.caption("Identifies multivariate statistical outliers that deviate from the normal cluster of works.")
            
        # Similar / Duplicate Works
        similar = p.get("similar_projects", [])
        if similar:
            st.markdown("---")
            st.markdown("#### 🔁 Possible Duplicate / Overlapping Works Detected")
            for s in similar:
                col_sim_txt, col_sim_btn = st.columns([3, 1])
                col_sim_txt.info(f"Matched Group `{p.get('duplicate_group_id')}` | Work ID: `{s['project_id']}` — *{s['work_name']}* (Risk Score: {s['risk_score']})")
                if col_sim_btn.button("View Match", key=f"btn_sim_{s['project_id']}"):
                    st.session_state.selected_project = s['project_id']
                    st.rerun()

        # Provenance
        with st.expander("🔎 Audit Provenance & Source Traceability"):
            prov = p.get("provenance", {})
            st.json({
                "work_id": p.get("project_id"),
                "source_tables": prov.get("source_files"),
                "rule_version": prov.get("rule_version"),
                "ml_model_version": prov.get("model_version"),
                "active_features_evaluated": prov.get("features_used")
            })
            
        # Investigation Notes Workflow
        st.markdown("---")
        st.markdown("#### 📝 Auditor Investigation Workflow & Case Notes")
        
        with st.form("add_note_form", clear_on_submit=True):
            note_text = st.text_area("Add Observation or Field Audit Note:", placeholder="e.g., Requested expenditure vouchers from District Authority on 08/09...")
            author = st.text_input("Officer Name / Designation:", value="District Auditor")
            submitted = st.form_submit_button("Save Note to Dossier", type="primary")
            if submitted and note_text:
                post_api(f"/projects/{p['project_id']}/notes", {"note_text": note_text, "created_by": author})
                st.success("Note saved to database.")
                st.rerun()
                
        notes = p.get("notes", [])
        if notes:
            st.markdown("**Prior Investigation Notes:**")
            for n in notes:
                st.caption(f"📅 {n.get('created_at', '')[:19]} | **{n.get('created_by', 'Auditor')}:** {n.get('note_text')}")
        else:
            st.caption("No prior investigation notes logged for this project.")

# -------------------------------------------------------------
# SCREEN 4: GEO ANALYSIS
# -------------------------------------------------------------
elif st.session_state.page == "Geo Analysis":
    st.markdown("<div class='main-header'>🗺️ Geographic Risk Distribution</div>", unsafe_allow_html=True)
    
    states_res = fetch_api("/states")
    if states_res and states_res.get("data"):
        geo_summary = pd.DataFrame(states_res["data"])
        geo_summary["High_Plus_Critical"] = geo_summary["critical_count"] + geo_summary["high_count"]
        
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.subheader("State-Wise Risk Concentration")
            fig_geo_bar = px.bar(
                geo_summary, x="state", y="High_Plus_Critical",
                labels={"state": "State", "High_Plus_Critical": "High + Critical Works"},
                color="High_Plus_Critical",
                color_continuous_scale="Reds"
            )
            fig_geo_bar.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_geo_bar, width='stretch')
            
        with col_m2:
            st.subheader("Ranked State Statistics")
            geo_display = geo_summary[[
                "state", "total_works", "total_sanctioned", "total_spent", 
                "critical_count", "high_count", "avg_risk_score"
            ]].copy()
            geo_display["total_sanctioned"] = geo_display["total_sanctioned"].apply(lambda v: f"₹{v/1e7:.2f} Cr")
            geo_display["total_spent"] = geo_display["total_spent"].apply(lambda v: f"₹{v/1e7:.2f} Cr")
            geo_display["avg_risk_score"] = geo_display["avg_risk_score"].round(1)
            geo_display.rename(columns={
                "state": "State",
                "total_works": "Total Works",
                "total_sanctioned": "Sanctioned",
                "total_spent": "Spent",
                "critical_count": "Critical",
                "high_count": "High",
                "avg_risk_score": "Avg Risk"
            }, inplace=True)
            st.dataframe(geo_display, width='stretch', hide_index=True)
    else:
        st.warning("Unable to fetch geographic state summary.")

# -------------------------------------------------------------
# SCREEN 5: ML INSIGHTS
# -------------------------------------------------------------
elif st.session_state.page == "ML Insights":
    st.markdown("<div class='main-header'>🧠 Machine Learning Model Diagnostics</div>", unsafe_allow_html=True)
    
    projects_res = fetch_api("/projects", {"page_size": 1000})
    if projects_res and projects_res.get("data"):
        df = pd.DataFrame(projects_res["data"])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Model Architecture", "Isolation Forest")
        c2.metric("Trees (Estimators)", "200")
        c3.metric("Assumed Contamination", "5.0%")
        
        st.subheader("Multivariate Outlier Clustering (Expenditure vs Delay)")
        st.caption("Visualizing statistical separation between normal and anomalous work patterns.")
        
        plot_df = df[df["cost_overrun_ratio"].notnull()].copy()
        fig_scatter = px.scatter(
            plot_df,
            x="cost_overrun_ratio",
            y="delay_days",
            color="risk_category",
            size="ml_risk_score",
            hover_data=["project_id", "mp_name", "work_name", "risk_score"],
            labels={"cost_overrun_ratio": "Cost Overrun Ratio", "delay_days": "Delay in Days"},
            color_discrete_map={"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
        )
        fig_scatter.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_scatter, width='stretch')
    else:
        st.warning("Unable to load ML insights data.")

# Standing Mandatory Responsible AI Disclaimer
st.markdown("""
<div class='disclaimer'>
    ⚖️ <b>Regulatory & Responsible AI Notice:</b> All anomaly scores and flags surfaced by this system are analytical risk indicators intended to prioritize human investigation and audit resources. The system does not decide guilt, approve/reject sanctions, or prove fraud. Final determination rests with competent government authorities.
</div>
""", unsafe_allow_html=True)
