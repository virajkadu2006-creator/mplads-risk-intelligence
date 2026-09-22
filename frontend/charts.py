import streamlit as st
import plotly.express as px
import pandas as pd
from theme import apply_chart_theme

def render_risk_severity_donut(risk_counts, is_dark=True):
    """Render the risk severity donut chart on the Overview screen."""
    df_risk = pd.DataFrame(list(risk_counts.items()), columns=["Category", "Count"])
    fig = px.pie(
        df_risk, names="Category", values="Count", color="Category",
        color_discrete_map={"Critical": "#b91c1c", "High": "#ea580c", "Medium": "#eab308", "Low": "#16a34a"},
        hole=0.4
    )
    fig = apply_chart_theme(fig, is_dark)
    st.plotly_chart(fig, use_container_width=True)

def render_funds_overview_bar(total_sanctioned, total_spent, is_dark=True):
    """Render the sanctioned vs spent bar chart on the Overview screen."""
    funds_df = pd.DataFrame({
        "Type": ["Sanctioned", "Spent"],
        "Amount (₹ Cr)": [total_sanctioned / 1e7 if total_sanctioned else 0, 
                          total_spent / 1e7 if total_spent else 0]
    })
    fig = px.bar(
        funds_df, x="Type", y="Amount (₹ Cr)", color="Type", 
        color_discrete_sequence=["#3b82f6", "#0d9488"]
    )
    fig = apply_chart_theme(fig, is_dark)
    st.plotly_chart(fig, use_container_width=True)

def render_geo_bar(geo_summary, is_dark=True):
    """Render the state-wise risk concentration bar chart on Geo Analysis."""
    fig = px.bar(
        geo_summary, x="state", y="High_Plus_Critical",
        labels={"state": "State", "High_Plus_Critical": "High + Critical Works"},
        color="High_Plus_Critical",
        color_continuous_scale="Reds"
    )
    fig = apply_chart_theme(fig, is_dark)
    st.plotly_chart(fig, use_container_width=True)

def render_ml_scatter(df, is_dark=True):
    """Render the multivariate outlier scatter plot on ML Insights."""
    plot_df = df[df["cost_overrun_ratio"].notnull()].copy()
    fig = px.scatter(
        plot_df,
        x="cost_overrun_ratio",
        y="delay_days",
        color="risk_category",
        size="ml_risk_score",
        hover_data=["project_id", "mp_name", "work_name", "risk_score"],
        labels={"cost_overrun_ratio": "Cost Overrun Ratio", "delay_days": "Delay in Days"},
        color_discrete_map={"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}
    )
    fig = apply_chart_theme(fig, is_dark)
    st.plotly_chart(fig, use_container_width=True)
