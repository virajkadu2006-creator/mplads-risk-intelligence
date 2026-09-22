import streamlit as st

# Color Tokens
TOKENS = {
    "dark": {
        "bg": "#0f172a",
        "surface": "#1e293b",
        "surface_elevated": "#243146",
        "border": "#334155",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "primary": "#3b82f6",
        "risk_critical_text": "#fca5a5",
        "risk_critical_bg": "rgba(185, 28, 28, 0.25)",
        "risk_critical_border": "#ef4444",
        "risk_high_text": "#fdba74",
        "risk_high_bg": "rgba(234, 88, 12, 0.25)",
        "risk_high_border": "#f97316",
        "risk_medium_text": "#fde047",
        "risk_medium_bg": "rgba(234, 179, 8, 0.25)",
        "risk_medium_border": "#eab308",
        "risk_low_text": "#86efac",
        "risk_low_bg": "rgba(22, 163, 74, 0.25)",
        "risk_low_border": "#22c55e",
        "plotly_template": "plotly_dark",
    },
    "light": {
        "bg": "#f8fafc",
        "surface": "#ffffff",
        "surface_elevated": "#f1f5f9",
        "border": "#e2e8f0",
        "text": "#1e293b",
        "text_muted": "#64748b",
        "primary": "#3b82f6",
        "risk_critical_text": "#991b1b",
        "risk_critical_bg": "#fee2e2",
        "risk_critical_border": "#f87171",
        "risk_high_text": "#9a3412",
        "risk_high_bg": "#ffedd5",
        "risk_high_border": "#fb923c",
        "risk_medium_text": "#854d0e",
        "risk_medium_bg": "#fef9c3",
        "risk_medium_border": "#facc15",
        "risk_low_text": "#166534",
        "risk_low_bg": "#dcfce7",
        "risk_low_border": "#4ade80",
        "plotly_template": "plotly_white",
    }
}

def inject_theme(is_dark=True):
    theme = TOKENS["dark"] if is_dark else TOKENS["light"]
    
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {theme['bg']};
            color: {theme['text']};
        }}
        .main-header {{
            font-size: 26px;
            font-weight: 700;
            color: {theme['text']};
            margin-bottom: 20px;
        }}
        .section-header {{
            font-size: 20px;
            font-weight: 600;
            color: {theme['text']};
            margin-top: 24px;
            margin-bottom: 16px;
        }}
        .metric-card {{
            background: {theme['surface']};
            padding: 18px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            border: 1px solid {theme['border']};
            color: {theme['text']};
            transition: all 0.12s ease-in-out;
        }}
        .metric-card:hover {{
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border-color: {theme['text_muted']};
        }}
        .card-label {{
            font-size: 14px;
            color: {theme['text_muted']};
        }}
        .card-value {{
            font-size: 42px;
            font-weight: 800;
            color: {theme['text']};
        }}
        .evidence-card {{
            background: {theme['surface']};
            padding: 16px;
            border-radius: 8px;
            border: 1px solid {theme['border']};
            margin-bottom: 12px;
            transition: all 0.12s ease-in-out;
        }}
        .evidence-card:hover {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            border-color: {theme['text_muted']};
        }}
        .badge-critical {{
            background-color: {theme['risk_critical_bg']};
            color: {theme['risk_critical_text']};
            border: 1px solid {theme['risk_critical_border']};
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        .badge-high {{
            background-color: {theme['risk_high_bg']};
            color: {theme['risk_high_text']};
            border: 1px solid {theme['risk_high_border']};
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        .badge-medium {{
            background-color: {theme['risk_medium_bg']};
            color: {theme['risk_medium_text']};
            border: 1px solid {theme['risk_medium_border']};
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        .badge-low {{
            background-color: {theme['risk_low_bg']};
            color: {theme['risk_low_text']};
            border: 1px solid {theme['risk_low_border']};
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 12px;
        }}
        .disclaimer {{
            font-size: 12px;
            color: {theme['text_muted']};
            border-top: 1px solid {theme['border']};
            padding-top: 12px;
            margin-top: 30px;
        }}
    </style>
    """, unsafe_allow_html=True)

def apply_chart_theme(fig, is_dark=True):
    theme = TOKENS["dark"] if is_dark else TOKENS["light"]
    fig.update_layout(
        template=theme["plotly_template"],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def get_theme(is_dark=True):
    return TOKENS["dark"] if is_dark else TOKENS["light"]
