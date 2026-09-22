import streamlit as st
import plotly.express as px
import pandas as pd
from frontend.theme import apply_chart_theme, get_theme

def render_metric_card(label, value, sublabel=None, badge_text=None, badge_class=None):
    """Render a KPI metric card styled with CSS."""
    badge_html = f"<span class='{badge_class}' style='margin-left: 8px;'>{badge_text}</span>" if badge_text and badge_class else ""
    sublabel_html = f"<div style='font-size: 13px; color: var(--text-muted); margin-top: 4px;'>{sublabel}</div>" if sublabel else ""
    
    html = f"""
    <div class='metric-card' style='text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
        <div class='card-label'>{label}</div>
        <div class='card-value'>{value}{badge_html}</div>
        {sublabel_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_badge(risk_category):
    """Render a risk severity badge."""
    cat = risk_category.capitalize() if risk_category else "Low"
    color_class = "badge-critical" if cat == "Critical" else "badge-high" if cat == "High" else "badge-medium" if cat == "Medium" else "badge-low"
    return f"<span class='{color_class}'>{cat.upper()} RISK</span>"

def render_evidence_card(alert):
    """Render a structured evidence card for an alert."""
    sev = alert.get("severity", "Info")
    alert_type = alert.get("alert_type", "Unknown")
    reason = alert.get("reason_text", "")
    
    badge_class = "badge-critical" if sev == "Critical" else "badge-high" if sev == "High" else "badge-medium" if sev == "Medium" else "badge-low"
    
    html = f"""
    <div class='evidence-card'>
        <div style='margin-bottom: 8px;'>
            <span class='{badge_class}' style='margin-right: 8px;'>{sev.upper()} SEVERITY</span>
            <strong style='font-size: 14px;'>[{alert_type}]</strong>
        </div>
        <div style='font-size: 15px; line-height: 1.4;'>{reason}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_risk_breakdown_chart(project_row, weights, is_dark=True):
    """Render a horizontal stacked bar showing risk score composition."""
    
    theme = get_theme(is_dark)
    
    components = [
        {"name": "Cost Overrun", "val": project_row.get("cost_contribution", 0), "max": weights.get("cost", 25), "color": theme["risk_critical_text"]},
        {"name": "Timeline Delay", "val": project_row.get("delay_contribution", 0), "max": weights.get("delay", 25), "color": theme["risk_high_text"]},
        {"name": "ML Anomaly", "val": project_row.get("ml_contribution", 0), "max": weights.get("ml", 25), "color": theme["risk_medium_text"]},
        {"name": "Compliance", "val": project_row.get("compliance_contribution", 0), "max": weights.get("compliance", 25), "color": theme["primary"]},
        {"name": "Under-Utilization", "val": project_row.get("under_utilization_contribution", 0), "max": weights.get("under_utilization", 15), "color": theme["risk_low_text"]},
    ]
    
    df = pd.DataFrame(components)
    df["Project"] = "Risk Score" # Single bar
    
    fig = px.bar(
        df,
        x="val",
        y="Project",
        color="name",
        orientation='h',
        text="val",
        color_discrete_map={c["name"]: c["color"] for c in components},
        labels={"val": "Points", "name": "Risk Factor"}
    )
    
    fig.update_traces(textposition='inside', texttemplate='%{text:.1f}')
    fig.update_layout(
        barmode='stack',
        height=150,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[0, 100], fixedrange=True, title=None, showgrid=False),
        yaxis=dict(visible=False, fixedrange=True),
    )
    
    fig = apply_chart_theme(fig, is_dark)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Text summary for accessibility
    summary = ", ".join([f"{c['name']}: {c['val']:.1f}/{c['max']} pts" for c in components if c['val'] > 0])
    if not summary:
        summary = "No risk points accumulated."
    st.caption(f"**Score Breakdown:** {summary}")
