# ================================================================
# AI SUSTAINABILITY DASHBOARD  v4.1  (bug-fixed + enhanced)
# streamlit run app.py
# pip install streamlit pandas numpy plotly requests reportlab
# ================================================================

import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple   # ← use Tuple/Optional for Python <3.10 compat

# ================================================================
# PAGE CONFIG  — must be FIRST Streamlit call
# ================================================================
st.set_page_config(
    page_title="AI Sustainability Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================================================================
# CONSTANTS
# ================================================================
MODEL_SPECS = {
    "Claude Sonnet 4.6":  {"base_co2": 0.30, "base_power": 1.5, "efficiency": 0.88},
    "Claude Opus 4.6":    {"base_co2": 0.55, "base_power": 2.8, "efficiency": 0.75},
    "GPT-5.4":            {"base_co2": 0.50, "base_power": 2.5, "efficiency": 0.78},
    "Gemini 3.1 Pro":     {"base_co2": 0.42, "base_power": 2.1, "efficiency": 0.82},
    "Sonar":              {"base_co2": 0.22, "base_power": 1.1, "efficiency": 0.92},
    "Nemotron 3 Super":   {"base_co2": 0.60, "base_power": 3.0, "efficiency": 0.70},
}

CARBON_PRICE_PER_KG   = 0.02
TREE_ABSORPTION_KG_YR = 21.77
MAX_SIM_ITERATIONS    = 500
SLEEP_INTERVAL        = 0.7
AI_SUMMARY_INTERVAL   = 30

# ================================================================
# SIDEBAR
# ================================================================
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=True)

THEME = {
    "bg":      "#0a0d14" if dark_mode else "#f0f2f8",
    "card":    "#131720" if dark_mode else "#ffffff",
    "surface": "#1c2130" if dark_mode else "#eef0f7",
    "border":  "#2a3045" if dark_mode else "#d8dce8",
    "text":    "#e2e8f0" if dark_mode else "#1a2035",
    "muted":   "#64748b" if dark_mode else "#94a3b8",
    "accent":  "#38bdf8",
    "green":   "#34d399",
    "yellow":  "#fbbf24",
    "orange":  "#fb923c",
    "red":     "#f87171",
    "purple":  "#a78bfa",
    "pink":    "#f472b6",
    "plotly":  "plotly_dark" if dark_mode else "plotly_white",
}

st.sidebar.markdown("## ⚙️ Configuration")
st.sidebar.markdown(
    '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;'
    'letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;">Model</p>',
    unsafe_allow_html=True,
)
model = st.sidebar.selectbox("Model", list(MODEL_SPECS.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;'
    'letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;">Simulation</p>',
    unsafe_allow_html=True,
)
window    = st.sidebar.slider("Time Window (ticks)", 20, 100, 40)
intensity = st.sidebar.slider("Query Intensity", 1, 5, 3,
                               help="Multiplier applied to spike/boost modes")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;'
    'letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;">Alert Thresholds (kg CO₂)</p>',
    unsafe_allow_html=True,
)
co2_critical = st.sidebar.slider("🔴 Critical", 50, 120, 85)
co2_high     = st.sidebar.slider("🟠 High",     30, 100, 65)
co2_medium   = st.sidebar.slider("🟡 Medium",   20,  80, 45)

if not (co2_medium < co2_high < co2_critical):
    st.sidebar.error("Thresholds must satisfy: Medium < High < Critical")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;'
    'letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;">AI Engine</p>',
    unsafe_allow_html=True,
)
ANTHROPIC_API_KEY = st.sidebar.text_input(
    "Anthropic API Key", type="password", placeholder="sk-ant-...",
    help="Used only for AI Insights tab. Never stored.",
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="font-family:IBM Plex Mono,monospace;font-size:11px;'
    'letter-spacing:.1em;text-transform:uppercase;color:#38bdf8;">Quick Settings</p>',
    unsafe_allow_html=True,
)
show_forecast   = st.sidebar.checkbox("Show Forecast Band",    value=True)
show_anomalies  = st.sidebar.checkbox("Show Anomaly Markers",  value=True)
show_thresholds = st.sidebar.checkbox("Show Threshold Bands",  value=True)

# ================================================================
# CSS
# ================================================================
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');
  :root {{
    --bg:      {THEME['bg']};
    --card:    {THEME['card']};
    --surface: {THEME['surface']};
    --border:  {THEME['border']};
    --text:    {THEME['text']};
    --muted:   {THEME['muted']};
    --accent:  {THEME['accent']};
    --green:   {THEME['green']};
    --yellow:  {THEME['yellow']};
    --orange:  {THEME['orange']};
    --red:     {THEME['red']};
    --purple:  {THEME['purple']};
    --pink:    {THEME['pink']};
  }}
  html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text);
  }}
  h1, h2, h3 {{
    font-family: 'IBM Plex Mono', monospace;
    color: var(--accent); letter-spacing: -0.02em;
  }}
  h1 {{ font-size: 1.75rem; font-weight: 600; }}
  h2 {{ font-size: 1.25rem; font-weight: 600; }}
  h3 {{ font-size: 1.05rem; font-weight: 600; margin-top: 1.4rem; }}
  [data-testid="stSidebar"] {{
    background: var(--card) !important;
    border-right: 1px solid var(--border);
  }}
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stMarkdown p {{
    font-size: 13px; color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
  }}
  [data-testid="stMetric"] {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px !important;
    border-top: 3px solid var(--accent);
    transition: all 0.25s ease;
  }}
  [data-testid="stMetric"]:hover {{
    border-top-color: var(--green);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(56,189,248,0.12);
  }}
  [data-testid="stMetricLabel"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--muted) !important;
  }}
  [data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem; font-weight: 600; color: var(--text) !important;
  }}
  [data-testid="stMetricDelta"] {{ font-size: 12px; }}
  [data-baseweb="tab-list"] {{
    background: var(--surface); border-radius: 8px;
    padding: 4px; gap: 2px; border: 1px solid var(--border);
  }}
  [data-baseweb="tab"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px; letter-spacing: 0.05em;
    border-radius: 6px !important; padding: 6px 14px !important;
    color: var(--muted) !important; background: transparent !important;
    transition: all 0.18s ease;
  }}
  [aria-selected="true"][data-baseweb="tab"] {{
    background: var(--accent) !important; color: #000 !important; font-weight: 600;
  }}
  .stButton > button {{
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    letter-spacing: 0.05em; background: var(--surface);
    color: var(--text); border: 1px solid var(--border);
    border-radius: 7px; padding: 7px 16px; transition: all 0.18s ease;
  }}
  .stButton > button:hover {{
    border-color: var(--accent); color: var(--accent);
    background: var(--card); transform: translateY(-1px);
  }}
  .stDownloadButton > button {{
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    background: var(--accent); color: #000; border: none;
    border-radius: 7px; font-weight: 600;
  }}
  .stAlert {{
    border-radius: 8px; font-family: 'Sora', sans-serif;
    font-size: 13.5px; border-left-width: 4px;
  }}
  .stTextInput input, .stTextArea textarea {{
    font-family: 'IBM Plex Mono', monospace; font-size: 13px;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 7px; color: var(--text);
  }}
  .stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(56,189,248,0.15);
  }}
  [data-testid="stSelectbox"] > div > div {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 7px; font-family: 'IBM Plex Mono', monospace; font-size: 13px;
  }}
  [data-testid="stDataFrame"] {{
    border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
  }}
  hr {{ border-color: var(--border); margin: 1.2rem 0; }}
  .section-pill {{
    display: inline-block; background: var(--surface);
    border: 1px solid var(--border); border-radius: 20px; padding: 3px 12px;
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 10px;
  }}
  .status-badge {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 600;
  }}
  .chat-user {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px 10px 2px 10px; padding: 10px 14px;
    margin: 6px 0; font-size: 13.5px;
  }}
  .chat-ai {{
    background: rgba(56,189,248,0.08); border: 1px solid rgba(56,189,248,0.2);
    border-radius: 10px 10px 10px 2px; padding: 10px 14px;
    margin: 6px 0; font-size: 13.5px;
  }}
  .alert-entry {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; border-radius: 8px; margin: 5px 0;
    border: 1px solid var(--border); background: var(--card);
    font-family: 'IBM Plex Mono', monospace; font-size: 12px;
    transition: all 0.15s ease;
  }}
  .alert-entry:hover {{ border-color: var(--accent); }}
  .alert-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    margin-top: 4px; flex-shrink: 0;
  }}
  .alert-time {{ color: var(--muted); font-size: 11px; }}
  .alert-msg  {{ color: var(--text); }}
  .score-ring {{
    text-align: center; padding: 20px; background: var(--card);
    border: 1px solid var(--border); border-radius: 12px; margin: 4px;
    transition: all 0.2s ease;
  }}
  .score-ring:hover {{
    border-color: var(--accent);
    box-shadow: 0 4px 20px rgba(56,189,248,0.1);
  }}
  .score-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem; font-weight: 700; line-height: 1;
  }}
  .score-label {{
    font-family: 'IBM Plex Mono', monospace; font-size: 10px;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--muted); margin-top: 6px;
  }}
  .score-sub {{ font-size: 11px; color: var(--muted); margin-top: 4px; }}
  .proj-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px 20px; margin: 6px 0;
    border-left: 4px solid var(--accent);
  }}
  .proj-title {{
    font-family: 'IBM Plex Mono', monospace; font-size: 11px;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 6px;
  }}
  .proj-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem; font-weight: 700; color: var(--text);
  }}
  .proj-detail {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
  .custom-progress {{
    background: var(--surface); border-radius: 6px;
    height: 8px; overflow: hidden; margin: 6px 0;
  }}
  .custom-progress-fill {{
    height: 100%; border-radius: 6px; transition: width 0.4s ease;
  }}
  .info-tooltip {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 14px; font-size: 12px;
    color: var(--muted); font-family: 'IBM Plex Mono', monospace; margin: 6px 0;
  }}
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(1.15); }}
  }}
  .pulse-dot {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }}
  ::-webkit-scrollbar {{ width: 5px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--muted); }}
</style>
""", unsafe_allow_html=True)

# ================================================================
# SESSION STATE
# ================================================================
def _fresh_data() -> pd.DataFrame:
    """Bootstrap with integer tick column to avoid Timestamp issues."""
    n = 20
    return pd.DataFrame({
        "tick":    list(range(n)),
        "queries": np.random.randint(50, 100, n).astype(float),
        "co2":     np.random.randint(20, 50,  n).astype(float),
        "power":   np.random.randint(250, 350, n).astype(float),
    })

# All session state keys with plain (non-callable) defaults
_DEFAULTS = {
    "running":           False,
    "mode":              "normal",
    "data":              None,       # set below
    "session_start":     datetime.now(),
    "cumulative_co2":    0.0,
    "cumulative_power":  0.0,
    "total_queries":     0,
    "chat_history":      [],
    "last_ai_summary":   "",
    "last_summary_ts":   0.0,
    "last_co2_summary":  35.0,       # FIX: was getattr(_last_co2_for_summary)
    "alert_log":         [],
    "session_snapshots": [],
    "peak_co2":          0.0,
    "peak_power":        0.0,
    "peak_queries":      0,
    "total_alerts":      0,
    "uptime_ticks":      0,
    "tick_counter":      20,         # global monotonic tick index
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Initialise data separately (avoid re-calling on each key check)
if st.session_state["data"] is None:
    st.session_state["data"] = _fresh_data()

# ================================================================
# UTILITY FUNCTIONS
# ================================================================
def get_status(avg_co2: float) -> Tuple[str, str]:
    if avg_co2 > co2_critical: return "🔴 CRITICAL", THEME["red"]
    if avg_co2 > co2_high:     return "🟠 HIGH",     THEME["orange"]
    if avg_co2 > co2_medium:   return "🟡 MEDIUM",   THEME["yellow"]
    return "🟢 LOW", THEME["green"]


def efficiency_score(df: pd.DataFrame, mdl: str) -> float:
    spec = MODEL_SPECS[mdl]
    co2_per_q = df["co2"].mean() / max(df["queries"].mean(), 1)
    raw = 1 - (co2_per_q / 2.0)
    return round(max(0.0, min(100.0, raw * 100 * spec["efficiency"])), 1)


def trees_needed(co2_kg: float) -> float:
    return round(max(0.0, co2_kg) / TREE_ABSORPTION_KG_YR, 2)


def linear_forecast(series: pd.Series, steps: int = 10) -> np.ndarray:
    """Holt's double-exponential smoothing."""
    y = series.dropna().values.astype(float)
    if len(y) < 3:
        return np.full(steps, float(y[-1]) if len(y) else 0.0)
    alpha, beta = 0.4, 0.2
    level, trend = y[0], y[1] - y[0]
    for v in y[1:]:
        prev = level
        level = alpha * v + (1 - alpha) * (level + trend)
        trend = beta  * (level - prev)   + (1 - beta) * trend
    return np.array([level + i * trend for i in range(1, steps + 1)], dtype=float)


def call_claude(prompt: str,
                system: str = "You are an AI sustainability expert. Be concise and actionable.") -> str:
    if not ANTHROPIC_API_KEY:
        return "⚠️ Add your Anthropic API key in the sidebar to enable AI analysis."
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 512,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = r.json()
        if "content" in data and data["content"]:
            return data["content"][0]["text"]
        return f"Unexpected API response: {data.get('error', data)}"
    except requests.Timeout:
        return "⚠️ Request timed out. Try again."
    except Exception as exc:
        return f"API error: {exc}"


def export_pdf(df: pd.DataFrame) -> Optional[bytes]:  # FIX: was bytes | None (Python 3.10+)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buf  = BytesIO()
        doc  = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story  = []

        story.append(Paragraph("AI Sustainability Report", styles["Title"]))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Paragraph(f"Model: {model}", styles["Normal"]))
        story.append(Spacer(1, 12))

        rows = [
            ["Metric",              "Value"],
            ["Avg CO₂ (kg)",        round(df["co2"].mean(),  2)],
            ["Peak CO₂ (kg)",       int(df["co2"].max())],
            ["Avg Power (kWh)",     round(df["power"].mean(), 2)],
            ["Cumul. CO₂ (kg)",     round(st.session_state.cumulative_co2, 2)],
            ["Trees Needed/yr",     trees_needed(st.session_state.cumulative_co2)],
            ["Efficiency Score",    f"{efficiency_score(df, model)}/100"],
            ["Carbon Cost ($)",     f"${round(st.session_state.cumulative_co2 * CARBON_PRICE_PER_KG, 2)}"],
            ["Total Alerts",        st.session_state.total_alerts],
            ["Peak CO₂ (kg)",       round(st.session_state.peak_co2, 2)],
            ["Total Queries",       st.session_state.total_queries],
        ]

        t = Table(rows, colWidths=[220, 180])
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  colors.HexColor("#0c4a6e")),
            ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
        ]))
        story.append(t)

        story.append(Spacer(1, 20))
        story.append(Paragraph("Alert Log (last 10)", styles["Heading2"]))
        if st.session_state.alert_log:
            alert_rows = [["Time", "Level", "Message"]]
            for a in st.session_state.alert_log[-10:]:
                alert_rows.append([a.get("ts", ""), a.get("level", ""), a.get("message", "")])
            at = Table(alert_rows, colWidths=[120, 80, 200])
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
                ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID",       (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ]))
            story.append(at)

        doc.build(story)
        buf.seek(0)          # FIX: was missing seek(0) before read
        return buf.read()
    except ImportError:
        return None
    except Exception:
        return None


def log_alert(level: str, message: str, co2: float) -> None:
    entry = {
        "ts":      datetime.now().strftime("%H:%M:%S"),
        "level":   level,
        "message": message,
        "co2":     round(float(co2), 1),
        "model":   model,
    }
    st.session_state.alert_log.insert(0, entry)
    st.session_state.alert_log = st.session_state.alert_log[:200]
    st.session_state.total_alerts += 1


def compute_scorecard(df: pd.DataFrame, mdl: str) -> dict:
    eff    = efficiency_score(df, mdl)
    avg    = float(df["co2"].mean())
    stdv   = float(df["co2"].std()) if len(df) > 2 else 0.0
    stability   = max(0.0, min(100.0, 100 - (stdv / max(avg, 1)) * 100))
    co2_per_q   = avg / max(float(df["queries"].mean()), 1)
    carbon_int  = max(0.0, min(100.0, (1 - co2_per_q / 2.0) * 100))
    ticks       = max(st.session_state.uptime_ticks, 1)
    alert_rate  = st.session_state.total_alerts / ticks
    alert_score = max(0.0, min(100.0, (1 - alert_rate * 10) * 100))
    overall     = round(eff * 0.35 + stability * 0.25 + carbon_int * 0.25 + alert_score * 0.15, 1)
    return {
        "overall":    overall,
        "efficiency": eff,
        "stability":  round(stability, 1),
        "carbon_int": round(carbon_int, 1),
        "alert":      round(alert_score, 1),
    }


def score_color(v: float) -> str:
    if v >= 75: return THEME["green"]
    if v >= 50: return THEME["yellow"]
    if v >= 25: return THEME["orange"]
    return THEME["red"]


def cost_projections(avg_co2_per_tick: float) -> dict:
    hourly_ticks = 3600 / max(SLEEP_INTERVAL, 0.1)
    daily  = avg_co2_per_tick * hourly_ticks * 24
    weekly = daily * 7
    monthly= daily * 30
    yearly = daily * 365
    return {
        "daily_co2":    round(daily,   1),
        "weekly_co2":   round(weekly,  1),
        "monthly_co2":  round(monthly, 1),
        "yearly_co2":   round(yearly,  1),
        "daily_cost":   round(daily   * CARBON_PRICE_PER_KG, 2),
        "weekly_cost":  round(weekly  * CARBON_PRICE_PER_KG, 2),
        "monthly_cost": round(monthly * CARBON_PRICE_PER_KG, 2),
        "yearly_cost":  round(yearly  * CARBON_PRICE_PER_KG, 2),
        "trees_daily":  trees_needed(daily),
        "trees_yearly": trees_needed(yearly),
    }


def _chart_base(height: int = 320, title: str = "") -> dict:
    return dict(
        height=height, template=THEME["plotly"],
        title=dict(text=title, font=dict(family="IBM Plex Mono", size=13)) if title else {},
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    font=dict(family="IBM Plex Mono", size=11)),
        margin=dict(l=10, r=10, t=48 if title else 20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor=THEME["border"]),
        yaxis=dict(showgrid=True, gridcolor=THEME["border"]),
    )


# ================================================================
# HEADER
# ================================================================
elapsed    = str(datetime.now() - st.session_state.session_start).split(".")[0]
mode_color = {
    "normal": THEME["green"], "spike": THEME["red"],
    "low":    THEME["accent"], "high": THEME["orange"],
}.get(st.session_state.mode, THEME["accent"])

live_pulse = (
    f'<span class="pulse-dot" style="background:{THEME["green"]};"></span>'
    if st.session_state.running else
    f'<span style="width:8px;height:8px;border-radius:50%;'
    f'background:{THEME["muted"]};display:inline-block;"></span>'
)

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;
            padding-bottom:12px;border-bottom:1px solid {THEME['border']};margin-bottom:16px;">
  <div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                letter-spacing:.12em;text-transform:uppercase;color:{THEME['muted']};
                margin-bottom:4px;">AI Sustainability Monitor · v4.1</div>
    <h1 style="margin:0;font-size:1.7rem;">⚡ Emissions Dashboard</h1>
  </div>
  <div style="text-align:right;font-family:'IBM Plex Mono',monospace;font-size:12px;
              color:{THEME['muted']};">
    <div style="display:flex;align-items:center;gap:6px;justify-content:flex-end;margin-bottom:3px;">
      {live_pulse}
      <span style="color:{THEME['green'] if st.session_state.running else THEME['muted']};">
        {'● LIVE' if st.session_state.running else '○ PAUSED'}
      </span>
    </div>
    <div>Model: <span style="color:{THEME['accent']}">{model}</span></div>
    <div>Session: <span style="color:{THEME['text']}">{elapsed}</span></div>
    <div>Mode: <span style="color:{mode_color};font-weight:600;text-transform:uppercase;">{st.session_state.mode}</span></div>
    <div>Alerts: <span style="color:{THEME['red'] if st.session_state.total_alerts > 5 else THEME['text']};">{st.session_state.total_alerts}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ================================================================
# METRICS ROW
# ================================================================
df          = st.session_state.data
latest      = df.iloc[-1]
avg_co2_now = float(df["co2"].tail(5).mean())
status_lbl, _ = get_status(avg_co2_now)
eff         = efficiency_score(df, model)
carbon_cost = st.session_state.cumulative_co2 * CARBON_PRICE_PER_KG
trees       = trees_needed(st.session_state.cumulative_co2)

def _delta(col: str) -> int:
    return int(df[col].iloc[-1] - df[col].iloc[-2]) if len(df) > 1 else 0

row1 = st.columns(6)
row1[0].metric("Queries / tick",  int(latest["queries"]), delta=_delta("queries"))
row1[1].metric("CO₂ (kg)",        f"{latest['co2']:.1f}", delta=_delta("co2"),    delta_color="inverse")
row1[2].metric("Power (kWh)",     f"{latest['power']:.0f}", delta=_delta("power"), delta_color="inverse")
row1[3].metric("System Status",   status_lbl)
row1[4].metric("Efficiency",      f"{eff}/100")
row1[5].metric("Carbon Cost",     f"${carbon_cost:.2f}")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

row2 = st.columns(5)
row2[0].metric("🌳 Trees / yr",    str(trees))
row2[1].metric("📦 Cumul. CO₂",   f"{st.session_state.cumulative_co2:.1f} kg")
row2[2].metric("⚡ Cumul. Power",  f"{st.session_state.cumulative_power:.0f} kWh")
row2[3].metric("🏔️ Peak CO₂",     f"{st.session_state.peak_co2:.1f} kg")
row2[4].metric("🔔 Alerts",        st.session_state.total_alerts)

# ================================================================
# CONTROLS
# ================================================================
st.markdown("<hr>", unsafe_allow_html=True)
ctl_left, ctl_right = st.columns(2)

with ctl_left:
    st.markdown('<div class="section-pill">Simulation Control</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶ Start", use_container_width=True):
            st.session_state.running = True
    with c2:
        if st.button("⏸ Pause", use_container_width=True):
            st.session_state.running = False
    with c3:
        if st.button("↺ Reset", use_container_width=True):
            for k, v in _DEFAULTS.items():
                st.session_state[k] = v
            st.session_state["data"] = _fresh_data()
            st.rerun()

with ctl_right:
    st.markdown('<div class="section-pill">System Behavior</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("⚠️ Spike",  use_container_width=True):
            st.session_state.mode = "spike"
            log_alert("HIGH", f"Manual spike mode activated on {model}", float(latest["co2"]))
    with b2:
        if st.button("📉 Reduce", use_container_width=True):
            st.session_state.mode = "low"
    with b3:
        if st.button("🚀 Boost",  use_container_width=True):
            st.session_state.mode = "high"
            log_alert("MEDIUM", "Boost mode activated — increased load expected", float(latest["co2"]))
    with b4:
        if st.button("✅ Normal", use_container_width=True):
            st.session_state.mode = "normal"

st.markdown("<hr>", unsafe_allow_html=True)

# ================================================================
# TABS
# ================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⚡ Real-Time",
    "📊 Analytics",
    "📈 Advanced",
    "🧠 AI Insights",
    "🤖 Model Compare",
    "🚨 Alert Log",
    "🎯 Score & Projections",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 · REAL-TIME
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-pill">Live System Monitoring</div>', unsafe_allow_html=True)

    chart_ph      = st.empty()
    status_ph     = st.empty()
    data_table_ph = st.empty()

    spec = MODEL_SPECS[model]

    def _render_live(df_: pd.DataFrame, fc_x, fc_y, anom: pd.DataFrame, sl: str) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_["tick"], y=df_["co2"],
            name="CO₂ (kg)", mode="lines",
            line=dict(width=2.5, color=THEME["red"]),
            fill="tozeroy", fillcolor="rgba(248,113,113,0.07)",
        ))
        fig.add_trace(go.Scatter(
            x=df_["tick"], y=df_["queries"],
            name="Queries", mode="lines",
            line=dict(color=THEME["accent"], width=1.8),
        ))
        fig.add_trace(go.Scatter(
            x=df_["tick"], y=df_["power"],
            name="Power (kWh)", mode="lines",
            line=dict(color=THEME["green"], width=1.8),
        ))
        if show_forecast and len(fc_x):
            fig.add_trace(go.Scatter(
                x=fc_x, y=fc_y.tolist(),
                name="CO₂ Forecast", mode="lines",
                line=dict(color=THEME["orange"], dash="dot", width=2),
            ))
            upper = (fc_y * 1.10).tolist()
            lower = (fc_y * 0.90).tolist()
            fig.add_trace(go.Scatter(
                x=fc_x + fc_x[::-1],
                y=upper + lower[::-1],
                fill="toself", fillcolor="rgba(251,146,60,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Forecast Band", showlegend=False,
            ))
        if show_anomalies and not anom.empty:
            fig.add_trace(go.Scatter(
                x=anom["tick"], y=anom["co2"],
                mode="markers", name="Anomaly",
                marker=dict(size=10, color=THEME["red"], symbol="x",
                            line=dict(width=2, color="#fff")),
            ))
        if show_thresholds:
            for y0, y1, c in [
                (0,            co2_medium,   THEME["green"]),
                (co2_medium,   co2_high,     THEME["yellow"]),
                (co2_high,     co2_critical, THEME["orange"]),
                (co2_critical, 200,          THEME["red"]),
            ]:
                fig.add_hrect(y0=y0, y1=y1, fillcolor=c, opacity=0.05, line_width=0)
        fig.update_layout(**_chart_base(430, f"Live Monitor · {sl} · {model}"))
        return fig

    if st.session_state.running:
        tick = int(st.session_state.tick_counter)
        for _ in range(MAX_SIM_ITERATIONS):
            mode_ = st.session_state.mode
            prev  = st.session_state.data.iloc[-1]

            base_q = float(prev["queries"]) + np.random.uniform(-10, 10)
            if mode_ == "spike":
                base_q += np.random.randint(40, 80) * intensity
            elif mode_ == "low":
                base_q -= np.random.randint(20, 40)
            elif mode_ == "high":
                base_q += np.random.randint(20, 50) * intensity

            queries = float(np.clip(base_q, 10, 220))
            noise   = np.random.uniform(-0.1, 0.2)
            co2     = float(np.clip(queries * spec["base_co2"]   * (1 + noise),        5, 150))
            power   = float(np.clip(queries * spec["base_power"] * (1 + noise * 0.5), 80, 600))

            # Update accumulators
            st.session_state.cumulative_co2   += co2
            st.session_state.cumulative_power += power
            st.session_state.total_queries    += int(queries)
            st.session_state.uptime_ticks     += 1
            st.session_state.tick_counter      = tick + 1

            if co2   > st.session_state.peak_co2:    st.session_state.peak_co2    = co2
            if power > st.session_state.peak_power:   st.session_state.peak_power  = power
            if queries > st.session_state.peak_queries: st.session_state.peak_queries = int(queries)

            new_row = {"tick": tick, "queries": queries, "co2": co2, "power": power}
            st.session_state.data = pd.concat(
                [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
            ).tail(window)
            tick += 1

            df_      = st.session_state.data.copy()
            avg_co2_ = float(df_["co2"].tail(5).mean())
            sl_, sc_ = get_status(avg_co2_)

            # Threshold-triggered alert logging (throttled)
            if co2 > co2_critical:
                log_alert("CRITICAL", f"CO₂ exceeded critical threshold: {co2:.1f}kg on {model}", co2)
            elif co2 > co2_high and np.random.random() < 0.15:
                log_alert("HIGH", f"CO₂ above high threshold: {co2:.1f}kg", co2)

            # Snapshot every 10 ticks
            if st.session_state.uptime_ticks % 10 == 0:
                st.session_state.session_snapshots.append({
                    "tick":    st.session_state.uptime_ticks,
                    "avg_co2": round(float(df_["co2"].mean()), 1),
                    "eff":     efficiency_score(df_, model),
                    "queries": int(df_["queries"].mean()),
                })
                st.session_state.session_snapshots = st.session_state.session_snapshots[-50:]

            status_ph.markdown(
                f'<div class="status-badge" style="background:rgba(0,0,0,.3);border:1px solid {sc_};">'
                f'<span style="color:{sc_};font-size:16px;">●</span>'
                f'<span style="color:{THEME["text"]};">System Status: </span>'
                f'<span style="color:{sc_};">{sl_}</span></div>',
                unsafe_allow_html=True,
            )

            # Anomaly detection
            roll_mean = df_["co2"].rolling(5, min_periods=1).mean()
            roll_std  = df_["co2"].rolling(5, min_periods=1).std().fillna(0)
            anom_     = df_[df_["co2"] > (roll_mean + 2 * roll_std)]

            fc_y = linear_forecast(df_["co2"], steps=8)
            last_tick = int(df_["tick"].iloc[-1])
            fc_x = list(range(last_tick + 1, last_tick + 9))  # FIX: int range, no Timedelta

            chart_ph.plotly_chart(_render_live(df_, fc_x, fc_y, anom_, sl_), use_container_width=True)

            # FIX: use .map() instead of deprecated .applymap()
            def _co2_style(val):
                if isinstance(val, (int, float)) and val > co2_high:
                    return f"color:{THEME['red']};font-weight:600"
                return ""

            styled = df_.tail(10).style.map(_co2_style, subset=["co2"])
            data_table_ph.dataframe(styled, use_container_width=True, height=240)

            # Auto AI summary — uses session_state key, not getattr
            co2_changed  = abs(co2 - st.session_state.last_co2_summary) > 10
            time_elapsed = time.time() - st.session_state.last_summary_ts > AI_SUMMARY_INTERVAL
            if ANTHROPIC_API_KEY and time_elapsed and co2_changed:
                st.session_state.last_co2_summary  = co2
                p = (
                    f"Metrics — CO₂: {co2:.1f}kg, Queries: {queries:.0f}, Power: {power:.0f}kWh, "
                    f"Model: {model}, Mode: {mode_}. 2-sentence sustainability insight."
                )
                st.session_state.last_ai_summary  = call_claude(p)
                st.session_state.last_summary_ts  = time.time()

            time.sleep(SLEEP_INTERVAL)
            if not st.session_state.running:
                break

    # Static render when paused
    df_  = st.session_state.data.copy()
    if not df_.empty:
        avg5     = float(df_["co2"].tail(5).mean())
        sl_, sc_ = get_status(avg5)
        status_ph.markdown(
            f'<div class="status-badge" style="background:rgba(0,0,0,.3);border:1px solid {sc_};">'
            f'<span style="color:{sc_};font-size:16px;">●</span>'
            f'<span style="color:{THEME["text"]};">System Status: </span>'
            f'<span style="color:{sc_};">{sl_}</span></div>',
            unsafe_allow_html=True,
        )
        fc_y      = linear_forecast(df_["co2"], steps=8)
        last_tick = int(df_["tick"].iloc[-1])
        fc_x      = list(range(last_tick + 1, last_tick + 9))
        anom_     = df_[df_["co2"] > (df_["co2"].rolling(5, min_periods=1).mean() + 2 * df_["co2"].rolling(5, min_periods=1).std().fillna(0))]
        chart_ph.plotly_chart(_render_live(df_, fc_x, fc_y, anom_, sl_), use_container_width=True)
        data_table_ph.dataframe(df_.tail(10), use_container_width=True, height=240)

    if st.session_state.last_ai_summary:
        st.info(f"🤖 **Auto AI Summary:** {st.session_state.last_ai_summary}")


# ══════════════════════════════════════════════════════════════════
# TAB 2 · ANALYTICS
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-pill">System Analytics</div>', unsafe_allow_html=True)
    df = st.session_state.data.copy()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg CO₂",    f"{df['co2'].mean():.2f} kg")
    m2.metric("Peak CO₂",   f"{df['co2'].max():.0f} kg")
    m3.metric("Avg Power",  f"{df['power'].mean():.1f} kWh")
    m4.metric("Efficiency", f"{efficiency_score(df, model)}/100")

    st.markdown("### 📈 Smoothed Trends (5-tick rolling avg)")
    roll = df.set_index("tick")[["co2", "queries", "power"]].rolling(5, min_periods=1).mean()
    fig_t = go.Figure()
    for col, color in [("co2", THEME["red"]), ("queries", THEME["accent"]), ("power", THEME["green"])]:
        fig_t.add_trace(go.Scatter(x=roll.index, y=roll[col], name=col.capitalize(),
                                    mode="lines", line=dict(color=color, width=2)))
    fig_t.update_layout(**_chart_base(320))
    st.plotly_chart(fig_t, use_container_width=True)

    st.markdown("### 📊 CO₂ Distribution")
    fig_h = go.Figure()
    fig_h.add_trace(go.Histogram(x=df["co2"], nbinsx=20,
                                  marker_color=THEME["accent"], opacity=0.75, name="CO₂"))
    fig_h.add_vline(x=float(df["co2"].mean()), line_color=THEME["green"], line_dash="dash",
                     annotation_text="Mean", annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_h.add_vline(x=co2_critical, line_color=THEME["red"], line_dash="dot",
                     annotation_text="Critical", annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_h.update_layout(**_chart_base(280, "CO₂ Distribution"))
    st.plotly_chart(fig_h, use_container_width=True)

    st.markdown("### 🔮 CO₂ Forecast — Next 10 Ticks (Holt's Smoothing)")
    fc_vals  = linear_forecast(df["co2"], steps=10)
    last_idx = int(df["tick"].max())
    fig_fc   = go.Figure()
    fig_fc.add_trace(go.Scatter(x=df["tick"].tolist(), y=df["co2"].tolist(),
                                 name="Historical", line=dict(color=THEME["red"], width=2)))
    fig_fc.add_trace(go.Scatter(x=list(range(last_idx + 1, last_idx + 11)), y=fc_vals.tolist(),
                                 name="Forecast", mode="lines+markers",
                                 line=dict(color=THEME["orange"], dash="dot", width=2),
                                 marker=dict(size=5)))
    fig_fc.update_layout(**_chart_base(300))
    st.plotly_chart(fig_fc, use_container_width=True)

    st.markdown("### 🔗 Feature Correlation")
    corr    = df[["queries", "co2", "power"]].corr()
    fig_cor = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns.tolist(), y=corr.columns.tolist(),
        colorscale="RdBu", zmid=0,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}", textfont=dict(family="IBM Plex Mono", size=13),
    ))
    fig_cor.update_layout(**_chart_base(280))
    st.plotly_chart(fig_cor, use_container_width=True)

    cum = st.session_state.cumulative_co2
    st.info(
        f"**Session CO₂: {cum:.1f} kg** — "
        f"requires **{trees_needed(cum)} trees/yr** to offset. "
        f"Carbon cost @ ${CARBON_PRICE_PER_KG}/kg: **${cum * CARBON_PRICE_PER_KG:.2f}**"
    )


# ══════════════════════════════════════════════════════════════════
# TAB 3 · ADVANCED
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-pill">Advanced Insights</div>', unsafe_allow_html=True)
    df = st.session_state.data.copy()
    for col in ["queries", "co2", "power"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    df["idx"] = df.index

    if len(df) < 8:
        st.warning("⚠️ Start the simulation to generate enough data for advanced visualisations.")
    else:
        sample = df.iloc[::max(1, len(df) // 60)]

        st.markdown("### 🌐 3D System View")
        fig3d = px.scatter_3d(
            sample, x="idx", y="queries", z="co2",
            color="power", size="queries",
            color_continuous_scale="Turbo", opacity=0.85,
        )
        fig3d.update_traces(marker=dict(size=5))
        fig3d.update_layout(
            template=THEME["plotly"], height=460,
            scene=dict(xaxis_title="Tick", yaxis_title="Queries", zaxis_title="CO₂",
                       bgcolor="rgba(0,0,0,0)"),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig3d, use_container_width=True)

        cl, cr = st.columns(2)
        with cl:
            st.markdown("### 🔵 Load vs Emissions")
            fig_b = px.scatter(df, x="queries", y="co2", size="power", color="power",
                               color_continuous_scale="Turbo",
                               labels={"queries": "Query Load", "co2": "CO₂ (kg)"})
            fig_b.update_layout(**_chart_base(340))
            st.plotly_chart(fig_b, use_container_width=True)

        with cr:
            st.markdown("### ⚡ CO₂ Stress Gauge")
            stress = float(np.clip(df["co2"].iloc[-1], 0, 120))
            gauge  = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=stress,
                delta={"reference": float(df["co2"].mean()), "increasing": {"color": THEME["red"]}},
                title={"text": "CO₂ Stress", "font": {"family": "IBM Plex Mono", "size": 14}},
                number={"font": {"family": "IBM Plex Mono"}, "suffix": " kg"},
                gauge={
                    "axis":  {"range": [0, 120], "tickfont": {"family": "IBM Plex Mono", "size": 10}},
                    "bar":   {"color": THEME["red"]},
                    "steps": [
                        {"range": [0,            co2_medium],   "color": "rgba(52,211,153,.25)"},
                        {"range": [co2_medium,   co2_high],     "color": "rgba(251,191,36,.25)"},
                        {"range": [co2_high,     co2_critical], "color": "rgba(251,146,60,.25)"},
                        {"range": [co2_critical, 120],          "color": "rgba(248,113,113,.25)"},
                    ],
                    "threshold": {"line": {"color": THEME["orange"], "width": 3},
                                  "thickness": 0.75, "value": co2_critical},
                },
            ))
            gauge.update_layout(height=340, template=THEME["plotly"],
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(l=20, r=20, t=30, b=10))
            st.plotly_chart(gauge, use_container_width=True)

        st.markdown("### 🔋 Power Efficiency Trend")
        df["co2_per_q"]   = df["co2"]   / df["queries"].replace(0, 1)
        df["power_per_q"] = df["power"] / df["queries"].replace(0, 1)
        fig_eff = go.Figure()
        for col, name, color in [
            ("co2_per_q",   "CO₂/Query",   THEME["red"]),
            ("power_per_q", "Power/Query", THEME["purple"]),
        ]:
            fig_eff.add_trace(go.Scatter(
                x=df["idx"], y=df[col].rolling(5, min_periods=1).mean(),
                name=name, mode="lines", line=dict(color=color, width=2),
            ))
        fig_eff.update_layout(**_chart_base(260, "Per-Query Efficiency"))
        st.plotly_chart(fig_eff, use_container_width=True)

        st.markdown("### 🚨 Anomaly Detection")
        roll_m = df["co2"].rolling(5, min_periods=1).mean()
        roll_s = df["co2"].rolling(5, min_periods=1).std().fillna(0)
        anom   = df[df["co2"] > (roll_m + 1.5 * roll_s)]

        al, ar = st.columns([1, 3])
        with al:
            st.metric("Anomalies", len(anom))
            st.metric("Rate", f"{round(len(anom) / max(len(df), 1) * 100, 1)}%")
        with ar:
            if not anom.empty:
                fig_an = px.bar(anom, x="idx", y="co2", color="co2",
                                color_continuous_scale="Reds",
                                labels={"idx": "Tick", "co2": "CO₂ (kg)"})
                fig_an.update_layout(**_chart_base(260))
                st.plotly_chart(fig_an, use_container_width=True)
            else:
                st.success("✅ No anomalies detected in current window.")


# ══════════════════════════════════════════════════════════════════
# TAB 4 · AI INSIGHTS
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-pill">AI Decision Engine</div>', unsafe_allow_html=True)
    df       = st.session_state.data.copy()
    latest_  = df.iloc[-1]
    co2_v    = float(latest_["co2"])
    q_v      = float(latest_["queries"])
    pw_v     = float(latest_["power"])
    trend_v  = float(df["co2"].tail(5).mean()) - float(df["co2"].head(5).mean())

    if co2_v > co2_critical:
        st.error("🚨 **Critical System State** — Immediate action required"); risk = "HIGH"
    elif co2_v > co2_medium:
        st.warning("⚠️ **Moderate Risk** — Monitor and optimise"); risk = "MEDIUM"
    else:
        st.success("✅ **Healthy System** — Operating within acceptable thresholds"); risk = "LOW"

    if trend_v > 10:    st.warning("📈 **CO₂ Trend:** Increasing — intervention may be needed")
    elif trend_v < -10: st.success("📉 **CO₂ Trend:** Decreasing — optimisations are working")
    else:               st.info("➡️ **CO₂ Trend:** Stable")

    fc_next = float(linear_forecast(df["co2"], steps=1)[0])
    fi1, fi2 = st.columns(2)
    fi1.metric("🔮 Predicted CO₂ (next)", f"{fc_next:.1f} kg",
               delta=f"{fc_next - co2_v:+.1f}", delta_color="inverse")
    fi2.metric("📊 Risk Level", risk)

    st.markdown("### 🤖 Recommendations")
    spec_ = MODEL_SPECS[model]
    recs_map = {
        "HIGH": [
            "Shift workloads to off-peak hours to leverage lower-carbon grid periods.",
            "Enable model compression / quantisation to cut per-query footprint.",
            "Reduce concurrent query load — consider request queuing.",
            f"Switch to a lighter model (e.g. **Sonar** at 0.22 kg/query vs {spec_['base_co2']} kg).",
        ],
        "MEDIUM": [
            "Optimise request batching to reduce per-query overhead.",
            "Review query routing — eliminate redundant model calls.",
            "Schedule heavy workloads during renewable-heavy grid windows.",
        ],
        "LOW": [
            "Maintain current configuration — system is healthy.",
            "Continue monitoring for drift in query patterns.",
            "Explore further gains with response caching or prompt compression.",
        ],
    }
    for i, r in enumerate(recs_map[risk], 1):
        st.markdown(f"**{i}.** {r}")

    st.markdown("### 🧪 Scenario Simulation")
    sc1, sc2 = st.columns([1, 2])
    with sc1:
        scenario = st.selectbox("Choose Scenario", ["Peak Load", "Optimized", "Balanced"])
    scenarios_cfg = {
        "Peak Load":  (THEME["red"],    "High CO₂ spike expected. Stress gauge enters critical zone."),
        "Optimized":  (THEME["green"],  "Reduced emissions. Efficiency score improves significantly."),
        "Balanced":   (THEME["accent"], "Moderate load. Stable emissions and predictable performance."),
    }
    color_s, msg_s = scenarios_cfg[scenario]
    with sc2:
        st.markdown(
            f'<div style="background:rgba(0,0,0,.2);border:1px solid {color_s};'
            f'border-radius:8px;padding:10px 14px;font-family:IBM Plex Mono,monospace;'
            f'font-size:13px;color:{color_s};">{msg_s}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 📐 Model Efficiency Benchmark")
    curr_co2_per_q = co2_v / max(q_v, 1)
    bench = pd.DataFrame([
        {"Model": m, "CO₂/Query": sp["base_co2"]}
        for m, sp in MODEL_SPECS.items()
    ])
    fig_bm = px.bar(bench, x="Model", y="CO₂/Query",
                    color="CO₂/Query", color_continuous_scale="RdYlGn_r",
                    text="CO₂/Query")
    fig_bm.add_hline(y=curr_co2_per_q, line_color=THEME["purple"], line_dash="dash",
                      annotation_text=f"Current avg: {curr_co2_per_q:.3f}",
                      annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_bm.update_traces(textposition="outside",
                          textfont=dict(family="IBM Plex Mono", size=10))
    fig_bm.update_layout(**_chart_base(320))
    st.plotly_chart(fig_bm, use_container_width=True)

    st.markdown("### 💬 AI Sustainability Expert Chat")
    for msg in st.session_state.chat_history[-20:]:
        css = "chat-user" if msg["role"] == "user" else "chat-ai"
        lbl = "You" if msg["role"] == "user" else "🤖 AI"
        st.markdown(f'<div class="{css}"><strong>{lbl}</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True)

    query = st.text_area("Question", label_visibility="collapsed", height=90,
                          placeholder="e.g. How can I reduce CO₂ for this model at peak load?")
    q1, q2 = st.columns([3, 1])
    with q1:
        run_btn = st.button("🚀 Analyse", use_container_width=True)
    with q2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if run_btn and query.strip():
        prompt = (
            f"System — CO₂: {co2_v:.1f}kg, Queries: {q_v:.0f}, Power: {pw_v:.0f}kWh, "
            f"Model: {model}, Risk: {risk}, "
            f"Trend: {'increasing' if trend_v > 10 else 'decreasing' if trend_v < -10 else 'stable'}, "
            f"Cumul. CO₂: {st.session_state.cumulative_co2:.1f}kg. "
            f"Question: {query}"
        )
        with st.spinner("Analysing…"):
            resp = call_claude(prompt)
        st.session_state.chat_history.append({"role": "user",      "content": query})
        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        if len(st.session_state.chat_history) > 40:
            st.session_state.chat_history = st.session_state.chat_history[-40:]
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TAB 5 · MODEL COMPARE
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-pill">Model Comparison</div>', unsafe_allow_html=True)
    avg_q = max(float(st.session_state.data["queries"].mean()), 1)
    st.caption(f"Estimates based on current average query load: **{avg_q:.0f} queries/tick**")

    rows_c = []
    for m_n, sp in MODEL_SPECS.items():
        rows_c.append({
            "Model":            m_n,
            "Est. CO₂ (kg)":    round(avg_q * sp["base_co2"],  1),
            "Est. Power (kWh)": round(avg_q * sp["base_power"], 1),
            "Efficiency (%)":   round(sp["efficiency"] * 100,  1),
            "Carbon Cost ($)":  round(avg_q * sp["base_co2"] * CARBON_PRICE_PER_KG, 2),
        })
    cmp_df = pd.DataFrame(rows_c).sort_values("Est. CO₂ (kg)")

    def _hl(row):
        if row["Model"] == model:
            return [f"background-color:rgba(56,189,248,.12);color:{THEME['accent']};font-weight:600"] * len(row)
        return [""] * len(row)

    st.dataframe(cmp_df.style.apply(_hl, axis=1), use_container_width=True, height=260)

    mc1, mc2 = st.columns(2)
    with mc1:
        fig_c1 = px.bar(cmp_df, x="Model", y="Est. CO₂ (kg)",
                         color="Efficiency (%)", color_continuous_scale="RdYlGn",
                         text="Est. CO₂ (kg)", title="CO₂ Emissions by Model")
        fig_c1.update_traces(textposition="outside",
                              textfont=dict(family="IBM Plex Mono", size=11))
        fig_c1.update_layout(**_chart_base(380, "CO₂ by Model"))
        st.plotly_chart(fig_c1, use_container_width=True)

    with mc2:
        cats = ["Efficiency", "Low CO₂", "Low Power", "Cost Eff."]
        fig_rad = go.Figure()
        for m_n, sp in MODEL_SPECS.items():
            vals = [
                sp["efficiency"] * 100,
                (1 - sp["base_co2"]  / 0.60) * 100,
                (1 - sp["base_power"]/ 3.0)  * 100,
                (1 - sp["base_co2"]  / 0.60) * 100,
            ]
            vals = [max(0.0, v) for v in vals]
            fig_rad.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill="toself", name=m_n,
                opacity=0.7 if m_n == model else 0.35,
                line=dict(width=2.5 if m_n == model else 1),
            ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template=THEME["plotly"], height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(family="IBM Plex Mono", size=11)),
            margin=dict(l=30, r=30, t=30, b=30),
            title=dict(text="Multi-Metric Radar", font=dict(family="IBM Plex Mono", size=13)),
        )
        st.plotly_chart(fig_rad, use_container_width=True)

    best_m  = cmp_df.iloc[0]["Model"]
    worst_m = cmp_df.iloc[-1]["Model"]
    st.success(f"✅ Most efficient at current load: **{best_m}**")
    if model == worst_m:
        pct = round((1 - MODEL_SPECS[best_m]["base_co2"] / MODEL_SPECS[model]["base_co2"]) * 100)
        st.warning(f"⚠️ **{model}** has the highest estimated CO₂. Switch to **{best_m}** for ~**{pct}%** reduction.")


# ══════════════════════════════════════════════════════════════════
# TAB 6 · ALERT LOG
# ══════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-pill">Alert History & Event Log</div>', unsafe_allow_html=True)
    alert_log = st.session_state.alert_log

    a1, a2, a3, a4 = st.columns(4)
    total_     = len(alert_log)
    crit_c     = sum(1 for a in alert_log if a.get("level") == "CRITICAL")
    high_c     = sum(1 for a in alert_log if a.get("level") == "HIGH")
    med_c      = sum(1 for a in alert_log if a.get("level") == "MEDIUM")
    a1.metric("Total Events",     total_)
    a2.metric("🔴 Critical",      crit_c)
    a3.metric("🟠 High",          high_c)
    a4.metric("🟡 Medium / Info", med_c)

    st.markdown("---")
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        lvl_filter = st.selectbox("Filter by Level", ["All", "CRITICAL", "HIGH", "MEDIUM"])
    with fc2:
        mdl_filter = st.selectbox("Filter by Model", ["All"] + list(MODEL_SPECS.keys()))
    with fc3:
        if st.button("🗑️ Clear Log", use_container_width=True):
            st.session_state.alert_log    = []
            st.session_state.total_alerts = 0
            st.rerun()

    filtered = alert_log
    if lvl_filter != "All":
        filtered = [a for a in filtered if a.get("level") == lvl_filter]
    if mdl_filter != "All":
        filtered = [a for a in filtered if a.get("model") == mdl_filter]

    st.markdown(f'<div class="info-tooltip">Showing {len(filtered)} of {total_} events</div>',
                unsafe_allow_html=True)

    level_cfg = {
        "CRITICAL": (THEME["red"],    "🔴"),
        "HIGH":     (THEME["orange"], "🟠"),
        "MEDIUM":   (THEME["yellow"], "🟡"),
    }
    if not filtered:
        st.info("No events logged yet. Start the simulation to generate alerts.")
    else:
        for entry in filtered[:50]:
            lvl_   = entry.get("level", "INFO")
            c_, ic = level_cfg.get(lvl_, (THEME["muted"], "ℹ️"))
            st.markdown(f"""
            <div class="alert-entry">
              <div class="alert-dot" style="background:{c_};"></div>
              <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="color:{c_};font-weight:600;">{ic} {lvl_}</span>
                  <span class="alert-time">{entry.get('ts','')}</span>
                </div>
                <div class="alert-msg">{entry.get('message','')}</div>
                <div class="alert-time" style="margin-top:3px;">
                  CO₂: {entry.get('co2','—')} kg · Model: {entry.get('model','—')}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    if len(alert_log) >= 3:
        st.markdown("### 📊 Alert Frequency")
        al_df  = pd.DataFrame(alert_log)
        al_cnt = al_df.groupby("level").size().reset_index(name="count")
        fig_al = px.pie(al_cnt, names="level", values="count",
                         color="level",
                         color_discrete_map={"CRITICAL": THEME["red"],
                                             "HIGH": THEME["orange"],
                                             "MEDIUM": THEME["yellow"]},
                         hole=0.45)
        fig_al.update_layout(template=THEME["plotly"], height=300,
                              paper_bgcolor="rgba(0,0,0,0)",
                              legend=dict(font=dict(family="IBM Plex Mono", size=11)),
                              margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_al, use_container_width=True)

    if alert_log:
        al_csv = pd.DataFrame(alert_log).to_csv(index=False).encode()
        st.download_button("📁 Export Alert Log CSV", al_csv, "alert_log.csv",
                            mime="text/csv", use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# TAB 7 · SCORE & PROJECTIONS
# ══════════════════════════════════════════════════════════════════
with tab7:
    st.markdown('<div class="section-pill">Sustainability Scorecard & Cost Projections</div>',
                unsafe_allow_html=True)
    df = st.session_state.data.copy()

    st.markdown("### 🎯 Sustainability Scorecard")
    sc = compute_scorecard(df, model)

    def _score_card(label: str, value: float, detail: str) -> str:
        color = score_color(value)
        return (
            f'<div class="score-ring">'
            f'<div class="score-value" style="color:{color};">{value}</div>'
            f'<div class="score-label">{label}</div>'
            f'<div class="custom-progress">'
            f'<div class="custom-progress-fill" style="width:{int(value)}%;background:{color};"></div>'
            f'</div><div class="score-sub">{detail}</div></div>'
        )

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.markdown(_score_card("Overall",    sc["overall"],    "Composite"),   unsafe_allow_html=True)
    sc2.markdown(_score_card("Efficiency", sc["efficiency"], "CO₂/query"),   unsafe_allow_html=True)
    sc3.markdown(_score_card("Stability",  sc["stability"],  "Variance"),    unsafe_allow_html=True)
    sc4.markdown(_score_card("Carbon Int", sc["carbon_int"], "Intensity"),   unsafe_allow_html=True)
    sc5.markdown(_score_card("Alert Hlth", sc["alert"],      "Alert burden"),unsafe_allow_html=True)

    ov    = sc["overall"]
    grade = "A+" if ov>=90 else "A" if ov>=80 else "B" if ov>=70 else "C" if ov>=60 else "D" if ov>=50 else "F"
    gc    = score_color(ov)
    st.markdown(f"""
    <div style="text-align:center;padding:20px;background:var(--card);
                border:2px solid {gc};border-radius:12px;margin:12px 0;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                  letter-spacing:.15em;text-transform:uppercase;color:var(--muted);">
        Sustainability Grade</div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:4rem;
                  font-weight:700;color:{gc};line-height:1.1;">{grade}</div>
      <div style="font-size:13px;color:var(--muted);">
        {model} · {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.session_snapshots:
        st.markdown("### 📈 Score History")
        snap_df = pd.DataFrame(st.session_state.session_snapshots)
        fig_sn  = go.Figure()
        fig_sn.add_trace(go.Scatter(x=snap_df["tick"], y=snap_df["eff"],
                                     name="Efficiency", mode="lines+markers",
                                     line=dict(color=THEME["green"], width=2),
                                     marker=dict(size=5)))
        fig_sn.add_trace(go.Scatter(x=snap_df["tick"], y=snap_df["avg_co2"],
                                     name="Avg CO₂", mode="lines+markers",
                                     line=dict(color=THEME["red"], width=2),
                                     marker=dict(size=5), yaxis="y2"))
        fig_sn.update_layout(
            **_chart_base(300),
            yaxis=dict(title="Efficiency", gridcolor=THEME["border"]),
            yaxis2=dict(title="Avg CO₂ (kg)", overlaying="y", side="right",
                        gridcolor=THEME["border"]),
        )
        st.plotly_chart(fig_sn, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💰 Cost & Carbon Projections")
    proj = cost_projections(float(df["co2"].mean()))

    def _proj_card(title: str, co2_: float, cost_: float, t_: float, color: str) -> str:
        return (
            f'<div class="proj-card" style="border-left-color:{color};">'
            f'<div class="proj-title">{title}</div>'
            f'<div class="proj-value">${cost_}</div>'
            f'<div class="proj-detail">📦 {co2_} kg CO₂<br>🌳 {t_} trees/yr to offset</div>'
            f'</div>'
        )

    p1, p2, p3, p4 = st.columns(4)
    p1.markdown(_proj_card("Daily",   proj["daily_co2"],   proj["daily_cost"],   proj["trees_daily"],              THEME["green"]),  unsafe_allow_html=True)
    p2.markdown(_proj_card("Weekly",  proj["weekly_co2"],  proj["weekly_cost"],  trees_needed(proj["weekly_co2"]), THEME["accent"]), unsafe_allow_html=True)
    p3.markdown(_proj_card("Monthly", proj["monthly_co2"], proj["monthly_cost"], trees_needed(proj["monthly_co2"]),THEME["yellow"]), unsafe_allow_html=True)
    p4.markdown(_proj_card("Yearly",  proj["yearly_co2"],  proj["yearly_cost"],  proj["trees_yearly"],             THEME["red"]),    unsafe_allow_html=True)

    st.markdown("### 📊 Projected CO₂ Accumulation")
    periods   = ["Session", "Daily", "Weekly", "Monthly", "Yearly"]
    p_vals    = [round(st.session_state.cumulative_co2, 1),
                 proj["daily_co2"], proj["weekly_co2"], proj["monthly_co2"], proj["yearly_co2"]]
    fig_proj  = go.Figure(go.Bar(
        x=periods, y=p_vals,
        marker_color=[THEME["green"], THEME["accent"], THEME["yellow"], THEME["orange"], THEME["red"]],
        text=[f"{v} kg" for v in p_vals],
        textposition="outside", textfont=dict(family="IBM Plex Mono", size=11),
    ))
    fig_proj.update_layout(**_chart_base(300, "CO₂ Projections"))
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("### 🆚 Model Switch Savings")
    best_m_ = min(MODEL_SPECS.items(), key=lambda x: x[1]["base_co2"])[0]
    if model != best_m_:
        ratio   = MODEL_SPECS[best_m_]["base_co2"] / MODEL_SPECS[model]["base_co2"]
        save_co2  = round(proj["yearly_co2"]  * (1 - ratio), 1)
        save_cost = round(proj["yearly_cost"] * (1 - ratio), 2)
        cs1, cs2 = st.columns(2)
        cs1.success(
            f"💡 Switching to **{best_m_}** saves ~**{save_co2} kg CO₂/yr** "
            f"({round((1 - ratio) * 100)}% reduction)"
        )
        cs2.info(f"💰 Annual carbon cost saving: **${save_cost}**  \n"
                 f"🌳 Offset trees freed: **{trees_needed(save_co2)}**")
    else:
        st.success(f"✅ You're already on the most CO₂-efficient model: **{model}**")

# ================================================================
# EXPORT
# ================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-pill">Export</div>', unsafe_allow_html=True)

ex1, ex2, ex3 = st.columns(3)
with ex1:
    csv_b = st.session_state.data.to_csv(index=False).encode()
    st.download_button("📁 Download CSV", csv_b, "sustainability_data.csv",
                        mime="text/csv", use_container_width=True)
with ex2:
    pdf_b = export_pdf(st.session_state.data)
    if pdf_b:
        st.download_button("📄 Download PDF Report", pdf_b, "sustainability_report.pdf",
                            mime="application/pdf", use_container_width=True)
    else:
        st.info("Install `reportlab` for PDF export: `pip install reportlab`")
with ex3:
    if st.session_state.alert_log:
        al_b = pd.DataFrame(st.session_state.alert_log).to_csv(index=False).encode()
        st.download_button("🔔 Export Alert Log", al_b, "alert_log.csv",
                            mime="text/csv", use_container_width=True)
    else:
        st.button("🔔 Export Alert Log", disabled=True, use_container_width=True)

# ================================================================
# FOOTER
# ================================================================
sc_foot = compute_scorecard(st.session_state.data, model)
st.markdown(f"""
<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;
            padding:14px 20px;display:flex;justify-content:space-between;align-items:center;
            font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--muted);
            margin-top:1rem;">
  <span>v4.1 · AI Sustainability Dashboard</span>
  <span>Score: <strong style="color:{score_color(sc_foot['overall'])};">{sc_foot['overall']}/100</strong></span>
  <span>Uptime: {elapsed}</span>
  <span>Model: <strong style="color:var(--accent);">{model}</strong></span>
  <span>Queries: {st.session_state.total_queries:,}</span>
</div>
""", unsafe_allow_html=True)
