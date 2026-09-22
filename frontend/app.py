import os
import threading
import time
import streamlit as st
import pandas as pd
import yaml
import json

from theme import inject_theme
from api_client import fetch_api, post_api, load_name_lookup, API_URL
from components import render_metric_card, render_badge, render_evidence_card, render_risk_breakdown_chart
from charts import render_risk_severity_donut, render_funds_overview_bar, render_geo_bar, render_ml_scatter

# Auto-launcher for FastAPI backend
def ensure_backend_running():
    import requests
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

# Inject Theme
inject_theme(is_dark)

# Load config for weights
@st.cache_data
def load_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "thresholds.yaml")
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return {}

config_data = load_config()
risk_weights = config_data.get("risk_scoring", {}).get("weights", {"cost": 25, "delay": 25, "ml": 25, "compliance": 25, "under_utilization": 15})

# -------------------------------------------------------------
# SCREEN 1: OVERVIEW
# -------------------------------------------------------------
if st.session_state.page == "Overview":
    st.markdown("<div class='main-header'>📊 Executive Overview</div>", unsafe_allow_html=True)
    
    with st.spinner("Loading risk data..."):
        stats = fetch_api("/statistics")
        
    if stats:
        kpis = stats["kpis"]
        dq_raw = stats.get("data_quality", "{}")
        dq = json.loads(dq_raw) if isinstance(dq_raw, str) else dq_raw
        
        rc = kpis.get("risk_counts", {})
        high_crit = rc.get("High", 0) + rc.get("Critical", 0)
        raw_cov = float(dq.get('join_coverage_pct', 0))
        capped_cov = min(100.0, raw_cov)
        cov_str = f"{capped_cov:.1f}%" if capped_cov % 1 != 0 else f"{int(capped_cov)}%"
        
        # Flex KPI row
        st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: render_metric_card("Total Works Ingested", f"{kpis['total_works']:,}")
        with col2: render_metric_card("Total Sanctioned", f"₹{kpis['total_sanctioned']/1e7:.2f} Cr" if kpis['total_sanctioned'] else "₹0")
        with col3: render_metric_card("Total Expenditure", f"₹{kpis['total_spent']/1e7:.2f} Cr" if kpis['total_spent'] else "₹0")
        with col4: render_metric_card("High/Critical Risk", f"{high_crit}", sublabel=f"{rc.get('Critical', 0)} Critical")
        with col5: render_metric_card("Data Quality Score", f"{cov_str} Valid")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        col_pie, col_bar = st.columns([1, 1])
        
        with col_pie:
            st.markdown("<div class='section-header'>Risk Severity Breakdown</div>", unsafe_allow_html=True)
            render_risk_severity_donut(rc, is_dark)
            st.caption("Distribution of active projects across risk tiers.")
            
        with col_bar:
            st.markdown("<div class='section-header'>Funds Overview (Sanctioned vs Spent)</div>", unsafe_allow_html=True)
            render_funds_overview_bar(kpis['total_sanctioned'], kpis['total_spent'], is_dark)
            st.caption("Aggregate comparison of allocated vs utilized capital.")
            
        st.markdown("---")
        
        # New sections below charts
        col_list, col_feed = st.columns([2, 1])
        
        with col_list:
            st.markdown("<div class='section-header'>🔥 Top Risk Projects</div>", unsafe_allow_html=True)
            with st.spinner("Loading top projects..."):
                top_projects_res = fetch_api("/projects", {"sort": "risk_score", "order": "desc", "page_size": 8})
                
            if top_projects_res and top_projects_res.get("data"):
                df_top = pd.DataFrame(top_projects_res["data"])
                name_lookup = load_name_lookup()
                if name_lookup:
                    df_top["mp_name"] = df_top["project_id"].map(lambda pid: name_lookup.get(pid, {}).get("mp_name", df_top.loc[df_top["project_id"]==pid, "mp_name"].iloc[0] if (df_top["project_id"]==pid).any() else ""))
                
                df_top = df_top[["project_id", "risk_score", "work_name", "sanction_amount", "amount_spent"]]
                
                # Render using column config
                st.dataframe(
                    df_top,
                    column_config={
                        "project_id": "Work ID",
                        "risk_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                        "work_name": "Project Name",
                        "sanction_amount": st.column_config.NumberColumn("Sanction", format="₹%d"),
                        "amount_spent": st.column_config.NumberColumn("Spent", format="₹%d")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Navigate button below table
                selected_top_pid = st.selectbox("Inspect Project:", df_top["project_id"], key="top_proj_select", label_visibility="collapsed")
                if st.button("Open Investigation Dossier", key="btn_open_top"):
                    st.session_state.selected_project = selected_top_pid
                    st.session_state.page = "Project Investigation"
                    st.rerun()
            else:
                st.info("No high-risk projects found.")
                
            st.markdown("<div class='section-header'>💡 Actionable Insights</div>", unsafe_allow_html=True)
            with st.spinner("Generating insights..."):
                states_res = fetch_api("/states")
                
            if states_res and states_res.get("data"):
                states_df = pd.DataFrame(states_res["data"])
                if not states_df.empty:
                    states_df["High_Plus_Critical"] = states_df["critical_count"] + states_df["high_count"]
                    top_state = states_df.sort_values("High_Plus_Critical", ascending=False).iloc[0]
                    total_high_crit = states_df["High_Plus_Critical"].sum()
                    
                    if total_high_crit > 0:
                        concentration = (top_state["High_Plus_Critical"] / total_high_crit) * 100
                        st.info(f"**Geographic Risk:** {concentration:.1f}% of all high/critical risk works are concentrated in **{top_state['state']}**.")
                    
                    if kpis.get("total_spent") and kpis.get("total_sanctioned"):
                        avg_ratio = kpis["total_spent"] / kpis["total_sanctioned"] * 100
                        st.info(f"**Financial Trend:** The portfolio shows a {avg_ratio:.1f}% average fund utilization rate.")
        
        with col_feed:
            st.markdown("<div class='section-header'>🚨 Recent Anomalies</div>", unsafe_allow_html=True)
            with st.spinner("Loading anomalies..."):
                anomalies_res = fetch_api("/anomalies", {"limit": 6})
                
            if anomalies_res and anomalies_res.get("data"):
                for a in anomalies_res["data"]:
                    render_evidence_card(a)
                    if st.button(f"Investigate {a.get('project_id')}", key=f"btn_anom_{a.get('id')}", use_container_width=True):
                        st.session_state.selected_project = a.get("project_id")
                        st.session_state.page = "Project Investigation"
                        st.rerun()
            else:
                st.info("No recent anomalies found.")
                
        st.markdown("""
        <div class='disclaimer'>
            💡 <b>Auditor Workflow:</b> Go to <b>Risk Monitor</b> to inspect ranked candidate projects, or click <b>Project Investigation</b> to view evidence dossiers.
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# SCREEN 2: RISK MONITOR
# -------------------------------------------------------------
elif st.session_state.page == "Risk Monitor":
    st.markdown("<div class='main-header'>🔍 Risk Monitor (Global Ranked Projects)</div>", unsafe_allow_html=True)
    
    with st.spinner("Loading filters..."):
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
    
    with st.spinner("Loading projects..."):
        projects_res = fetch_api("/projects", params)
    
    if projects_res and projects_res.get("data"):
        data = projects_res["data"]
        df = pd.DataFrame(data)
        
        name_lookup = load_name_lookup()
        if name_lookup:
            df["mp_name"] = df["project_id"].map(lambda pid: name_lookup.get(pid, {}).get("mp_name", df.loc[df["project_id"]==pid, "mp_name"].iloc[0] if (df["project_id"]==pid).any() else ""))
            df["constituency"] = df["project_id"].map(lambda pid: name_lookup.get(pid, {}).get("constituency", ""))
        
        c_head1, c_head2 = st.columns([3, 1])
        c_head1.caption(f"Showing {len(df)} matching projects (sorted by Risk Score desc)")
        
        csv_data = df.to_csv(index=False)
        c_head2.download_button("📥 Download CSV", data=csv_data, file_name="mplads_risk_monitor.csv", mime="text/csv")
        
        display_df = df[[
            "project_id", "risk_score", "risk_category", "mp_name", 
            "constituency", "state", "district", "work_name", "sanction_amount", "amount_spent", "delay_days"
        ]].copy()
        
        st.dataframe(
            display_df,
            column_config={
                "project_id": "Work ID",
                "risk_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                "risk_category": "Risk Level",
                "mp_name": "MP Name",
                "constituency": "Constituency",
                "state": "State",
                "district": "District",
                "work_name": "Project Name",
                "sanction_amount": st.column_config.NumberColumn("Sanction", format="₹%d"),
                "amount_spent": st.column_config.NumberColumn("Spent", format="₹%d"),
                "delay_days": st.column_config.NumberColumn("Delay (Days)", format="%d")
            },
            width=None,
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("<div class='section-header'>🔎 Project Deep-Dive</div>", unsafe_allow_html=True)
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
    
    with st.spinner("Loading project list..."):
        all_proj_res = fetch_api("/projects", {"page_size": 200, "sort": "risk_score", "order": "desc"})
        
    all_projects = all_proj_res.get("data", []) if all_proj_res else []
    
    if all_projects:
        project_ids = [p["project_id"] for p in all_projects]
        id_to_label = {p["project_id"]: f"{p['project_id']} — {p['work_name']} [Score: {p['risk_score']}, {p['risk_category']}]" for p in all_projects}
        
        if "selected_project" not in st.session_state or st.session_state.selected_project not in id_to_label:
            st.session_state.selected_project = project_ids[0]
            
        current_idx = project_ids.index(st.session_state.selected_project) if st.session_state.selected_project in project_ids else 0
        selected_label = st.selectbox("Switch Project Dossier:", [id_to_label[pid] for pid in project_ids], index=current_idx)
        st.session_state.selected_project = selected_label.split(" — ")[0]
        selected_id = st.session_state.selected_project
    else:
        selected_id = st.session_state.get("selected_project", "W-1000")

    with st.spinner("Loading dossier..."):
        proj_res = fetch_api(f"/projects/{selected_id}")
        
    if proj_res and proj_res.get("data"):
        p = proj_res["data"]
        name_lookup = load_name_lookup()
        pid = p.get("project_id", "")
        if name_lookup and pid in name_lookup:
            p["mp_name"] = name_lookup[pid]["mp_name"]
            p["constituency"] = name_lookup[pid]["constituency"]
        
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
            render_metric_card("Composite Risk Score", f"{score}", sublabel="/100", badge_text=f"{cat.upper()} RISK", badge_class=f"badge-{cat.lower()}")
            
        st.markdown("---")
        
        # Alerts Box
        st.markdown("<div class='section-header'>🚨 Triggered Anomaly Signals</div>", unsafe_allow_html=True)
        alerts = p.get("alerts", [])
        if alerts:
            for a in alerts:
                render_evidence_card(a)
        else:
            st.success("No active threshold anomalies detected for this project.")
            
        # NEW: Risk Score Breakdown Chart
        st.markdown("<div class='section-header'>📊 Risk Score Breakdown</div>", unsafe_allow_html=True)
        render_risk_breakdown_chart(p, risk_weights, is_dark)
        
        st.markdown("---")
        
        # Financial & Timeline Panels
        col_fin, col_time = st.columns(2)
        with col_fin:
            st.markdown("<div class='section-header'>💰 Financial Panel</div>", unsafe_allow_html=True)
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
            st.markdown("<div class='section-header'>⏱️ Timeline & Progress Panel</div>", unsafe_allow_html=True)
            st.write(f"- **Recommended Date:** {p.get('date_recommended') or 'N/A'}")
            st.write(f"- **Sanction Date:** {p.get('sanction_date') or 'N/A'}")
            st.write(f"- **Project Age / Duration:** {p.get('delay_days') or 0} days")
            st.write(f"- **1-Year Norm Exceeded:** {'Yes (>365 days)' if p.get('delay_days', 0) > 365 else 'No (within norm)'}")
            
        st.markdown("---")
        
        # Peer Comparison & ML Insights
        col_peer, col_ml = st.columns(2)
        with col_peer:
            st.markdown("<div class='section-header'>👥 Peer Group Benchmarking</div>", unsafe_allow_html=True)
            peer = p.get("peer_comparison", {})
            st.write(f"- **Category:** `{peer.get('category')}`")
            cost_pct = peer.get("percentile_cost", 50)
            delay_pct = peer.get("percentile_delay", 50)
            st.metric("Cost Overrun Percentile", f"{cost_pct}th percentile", help="Percentile vs other projects in the same category")
            st.caption(f"Cost ratio is higher than **{cost_pct}%** of works in {peer.get('category')}.")
            st.metric("Timeline Delay Percentile", f"{delay_pct}th percentile")
            st.caption(f"Project duration is longer than **{delay_pct}%** of works in {peer.get('category')}.")
            
        with col_ml:
            st.markdown("<div class='section-header'>🤖 Unsupervised ML (Isolation Forest)</div>", unsafe_allow_html=True)
            ml_score = p.get("ml_risk_score") or 0.0
            st.metric("ML Anomaly Score", f"{ml_score:.1f}/100", help="Continuous score generated by Isolation Forest across 7 scaled features")
            st.write(f"- **Model:** `{p.get('model_version', 'isolation_forest_v1')}`")
            st.write(f"- **Trees:** 200 | **Contamination assumption:** 5% baseline")
            st.caption("Identifies multivariate statistical outliers that deviate from the normal cluster of works.")
            
        # Similar / Duplicate Works
        similar = p.get("similar_projects", [])
        if similar:
            st.markdown("---")
            st.markdown("<div class='section-header'>🔁 Possible Duplicate / Overlapping Works Detected</div>", unsafe_allow_html=True)
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
        st.markdown("<div class='section-header'>📝 Auditor Investigation Workflow & Case Notes</div>", unsafe_allow_html=True)
        
        with st.form("add_note_form", clear_on_submit=True):
            note_text = st.text_area("Add Observation or Field Audit Note:", placeholder="e.g., Requested expenditure vouchers from District Authority on 08/09...")
            author = st.text_input("Officer Name / Designation:", value="District Auditor")
            submitted = st.form_submit_button("Save Note to Dossier", type="primary")
            if submitted and note_text:
                post_api(f"/projects/{p['project_id']}/notes", {"note_text": note_text, "created_by": author})
                st.toast("Note saved to dossier! ✅") # Replaced st.success with st.toast
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
    
    with st.spinner("Loading geography data..."):
        states_res = fetch_api("/states")
        
    if states_res and states_res.get("data"):
        geo_summary = pd.DataFrame(states_res["data"])
        geo_summary["High_Plus_Critical"] = geo_summary["critical_count"] + geo_summary["high_count"]
        
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.markdown("<div class='section-header'>State-Wise Risk Concentration</div>", unsafe_allow_html=True)
            render_geo_bar(geo_summary, is_dark)
            st.caption("Total high and critical risk works per state.")
            
        with col_m2:
            st.markdown("<div class='section-header'>Ranked State Statistics</div>", unsafe_allow_html=True)
            geo_display = geo_summary[[
                "state", "total_works", "total_sanctioned", "total_spent", 
                "critical_count", "high_count", "avg_risk_score"
            ]].copy()
            
            st.dataframe(
                geo_display,
                column_config={
                    "state": "State",
                    "total_works": "Total Works",
                    "total_sanctioned": st.column_config.NumberColumn("Sanctioned", format="₹%d"),
                    "total_spent": st.column_config.NumberColumn("Spent", format="₹%d"),
                    "critical_count": "Critical",
                    "high_count": "High",
                    "avg_risk_score": st.column_config.NumberColumn("Avg Risk", format="%.1f")
                },
                width=None,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("Unable to fetch geographic state summary.")

# -------------------------------------------------------------
# SCREEN 5: ML INSIGHTS
# -------------------------------------------------------------
elif st.session_state.page == "ML Insights":
    st.markdown("<div class='main-header'>🧠 Machine Learning Model Diagnostics</div>", unsafe_allow_html=True)
    
    with st.spinner("Loading ML diagnostics..."):
        projects_res = fetch_api("/projects", {"page_size": 1000})
        
    if projects_res and projects_res.get("data"):
        df = pd.DataFrame(projects_res["data"])
        
        # Use CSS metric cards for the top row
        st.markdown("<div class='kpi-row'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: render_metric_card("Model Architecture", "Isolation Forest")
        with c2: render_metric_card("Trees (Estimators)", "200")
        with c3: render_metric_card("Assumed Contamination", "5.0%")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='section-header'>Multivariate Outlier Clustering (Expenditure vs Delay)</div>", unsafe_allow_html=True)
        render_ml_scatter(df, is_dark)
        st.caption("Visualizing statistical separation between normal and anomalous work patterns. Size of dot indicates ML Risk Score.")
    else:
        st.warning("Unable to load ML insights data.")

# Standing Mandatory Responsible AI Disclaimer
st.markdown("""
<div class='disclaimer'>
    ⚖️ <b>Regulatory & Responsible AI Notice:</b> All anomaly scores and flags surfaced by this system are analytical risk indicators intended to prioritize human investigation and audit resources. The system does not decide guilt, approve/reject sanctions, or prove fraud. Final determination rests with competent government authorities.
</div>
""", unsafe_allow_html=True)
