# ================= AI SUSTAINABILITY DASHBOARD v4 =================
# streamlit run app.py
# pip install streamlit pandas numpy plotly requests scikit-learn reportlab

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

# ================================================================
# CONFIG  (hardcoded — not user-editable at runtime)
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
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="AI Sustainability Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# THEME
# ================================================================
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=True)

THEME = {
    "bg":       "#0a0d14" if dark_mode else "#f0f2f8",
    "card":     "#131720" if dark_mode else "#ffffff",
    "surface":  "#1c2130" if dark_mode else "#eef0f7",
    "border":   "#2a3045" if dark_mode else "#d8dce8",
    "text":     "#e2e8f0" if dark_mode else "#1a2035",
    "muted":    "#64748b" if dark_mode else "#94a3b8",
    "accent":   "#38bdf8",
    "green":    "#34d399",
    "yellow":   "#fbbf24",
    "orange":   "#fb923c",
    "red":      "#f87171",
    "purple":   "#a78bfa",
    "pink":     "#f472b6",
    "plotly":   "plotly_dark" if dark_mode else "plotly_white",
}

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

  /* ---- Animated background grid ---- */
  .main .block-container {{
    padding-top: 1rem;
  }}

  /* ---- Typography ---- */
  h1, h2, h3 {{
    font-family: 'IBM Plex Mono', monospace;
    color: var(--accent);
    letter-spacing: -0.02em;
  }}
  h1 {{ font-size: 1.75rem; font-weight: 600; }}
  h2 {{ font-size: 1.25rem; font-weight: 600; }}
  h3 {{ font-size: 1.05rem; font-weight: 600; margin-top: 1.4rem; }}

  /* ---- Sidebar ---- */
  [data-testid="stSidebar"] {{
    background: var(--card) !important;
    border-right: 1px solid var(--border);
  }}
  [data-testid="stSidebar"] label,
  [data-testid="stSidebar"] .stMarkdown p {{
    font-size: 13px;
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
  }}
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 {{
    font-size: 13px;
    color: var(--accent);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}

  /* ---- Metric cards ---- */
  [data-testid="stMetric"] {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 18px !important;
    border-top: 3px solid var(--accent);
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
  }}
  [data-testid="stMetric"]:hover {{
    border-top-color: var(--green);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(56,189,248,0.12);
  }}
  [data-testid="stMetricLabel"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted) !important;
  }}
  [data-testid="stMetricValue"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text) !important;
  }}
  [data-testid="stMetricDelta"] {{ font-size: 12px; }}

  /* ---- Tabs ---- */
  [data-baseweb="tab-list"] {{
    background: var(--surface);
    border-radius: 8px;
    padding: 4px;
    gap: 2px;
    border: 1px solid var(--border);
  }}
  [data-baseweb="tab"] {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.05em;
    border-radius: 6px !important;
    padding: 6px 14px !important;
    color: var(--muted) !important;
    background: transparent !important;
    transition: all 0.18s ease;
  }}
  [aria-selected="true"][data-baseweb="tab"] {{
    background: var(--accent) !important;
    color: #000 !important;
    font-weight: 600;
  }}

  /* ---- Buttons ---- */
  .stButton > button {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.05em;
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 7px 16px;
    transition: all 0.18s ease;
  }}
  .stButton > button:hover {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--card);
    transform: translateY(-1px);
  }}

  /* ---- Download button ---- */
  .stDownloadButton > button {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 7px;
    font-weight: 600;
    transition: all 0.18s ease;
  }}
  .stDownloadButton > button:hover {{
    opacity: 0.85;
    transform: translateY(-1px);
  }}

  /* ---- Alerts / info boxes ---- */
  .stAlert {{
    border-radius: 8px;
    font-family: 'Sora', sans-serif;
    font-size: 13.5px;
    border-left-width: 4px;
  }}

  /* ---- Inputs ---- */
  .stTextInput input, .stTextArea textarea {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 7px;
    color: var(--text);
  }}
  .stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(56,189,248,0.15);
  }}

  /* ---- Selectbox ---- */
  [data-testid="stSelectbox"] > div > div {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
  }}

  /* ---- Dataframe ---- */
  [data-testid="stDataFrame"] {{
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}

  /* ---- Divider ---- */
  hr {{ border-color: var(--border); margin: 1.2rem 0; }}

  /* ---- Section header pill ---- */
  .section-pill {{
    display: inline-block;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 12px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
  }}

  /* ---- Status badge ---- */
  .status-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-weight: 600;
  }}

  /* ---- Chat bubbles ---- */
  .chat-user {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px 10px 2px 10px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13.5px;
  }}
  .chat-ai {{
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.2);
    border-radius: 10px 10px 10px 2px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size: 13.5px;
  }}

  /* ---- NEW: Alert log entry ---- */
  .alert-entry {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    border-radius: 8px;
    margin: 5px 0;
    border: 1px solid var(--border);
    background: var(--card);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    transition: all 0.15s ease;
  }}
  .alert-entry:hover {{ border-color: var(--accent); }}
  .alert-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    margin-top: 4px; flex-shrink: 0;
  }}
  .alert-time {{ color: var(--muted); font-size: 11px; }}
  .alert-msg {{ color: var(--text); }}

  /* ---- NEW: Scorecard ---- */
  .score-ring {{
    text-align: center;
    padding: 20px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin: 4px;
    transition: all 0.2s ease;
  }}
  .score-ring:hover {{
    border-color: var(--accent);
    box-shadow: 0 4px 20px rgba(56,189,248,0.1);
  }}
  .score-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
  }}
  .score-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-top: 6px;
  }}
  .score-sub {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
  }}

  /* ---- NEW: Cost projection card ---- */
  .proj-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin: 6px 0;
    border-left: 4px solid var(--accent);
  }}
  .proj-title {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
  }}
  .proj-value {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text);
  }}
  .proj-detail {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 4px;
  }}

  /* ---- NEW: Progress bar custom ---- */
  .custom-progress {{
    background: var(--surface);
    border-radius: 6px;
    height: 8px;
    overflow: hidden;
    margin: 6px 0;
  }}
  .custom-progress-fill {{
    height: 100%;
    border-radius: 6px;
    transition: width 0.4s ease;
  }}

  /* ---- NEW: Pulse animation for live indicator ---- */
  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(1.15); }}
  }}
  .pulse-dot {{
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }}

  /* ---- NEW: Glow effect on critical status ---- */
  @keyframes glow-red {{
    0%, 100% {{ box-shadow: 0 0 5px rgba(248,113,113,0.4); }}
    50% {{ box-shadow: 0 0 20px rgba(248,113,113,0.8); }}
  }}
  .glow-critical {{
    animation: glow-red 2s ease-in-out infinite;
    border-color: var(--red) !important;
  }}

  /* ---- NEW: Tooltip-style info box ---- */
  .info-tooltip {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: var(--muted);
    font-family: 'IBM Plex Mono', monospace;
    margin: 6px 0;
  }}

  /* ---- Sparkline mini badge ---- */
  .mini-stat {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 12px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: var(--text);
  }}

  /* ---- Scrollbar ---- */
  ::-webkit-scrollbar {{ width: 5px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: var(--muted); }}
</style>
""", unsafe_allow_html=True)

# ================================================================
# SIDEBAR
# ================================================================
st.sidebar.markdown("## ⚙️ Configuration")

st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">Model</p>', unsafe_allow_html=True)
model = st.sidebar.selectbox("Model", list(MODEL_SPECS.keys()), label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">Simulation</p>', unsafe_allow_html=True)
window    = st.sidebar.slider("Time Window (ticks)", 20, 100, 40)
intensity = st.sidebar.slider("Query Intensity", 1, 5, 3,
                               help="Multiplier applied to spike/boost modes")

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">Alert Thresholds (kg CO₂)</p>', unsafe_allow_html=True)
co2_critical = st.sidebar.slider("🔴 Critical", 50, 120, 85)
co2_high     = st.sidebar.slider("🟠 High",     30, 100, 65)
co2_medium   = st.sidebar.slider("🟡 Medium",   20,  80, 45)

if not (co2_medium < co2_high < co2_critical):
    st.sidebar.error("Thresholds must satisfy: Medium < High < Critical")

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">AI Engine</p>', unsafe_allow_html=True)
ANTHROPIC_API_KEY = st.sidebar.text_input(
    "Anthropic API Key", type="password", placeholder="sk-ant-...",
    help="Used only for AI Insights tab and auto-summaries. Never stored.",
    label_visibility="collapsed"
)

# ---- NEW: Sidebar quick stats ----
st.sidebar.markdown("---")
st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">Quick Settings</p>', unsafe_allow_html=True)
show_forecast     = st.sidebar.checkbox("Show Forecast Band", value=True)
show_anomalies    = st.sidebar.checkbox("Show Anomaly Markers", value=True)
show_thresholds   = st.sidebar.checkbox("Show Threshold Bands", value=True)
auto_export       = st.sidebar.checkbox("Auto-save Session Log", value=False)
query_rate_hours  = st.sidebar.number_input("Queries/Hour (for projections)", min_value=100, max_value=100000, value=5000, step=500)

# ================================================================
# SESSION STATE
# ================================================================
def fresh_data() -> pd.DataFrame:
    return pd.DataFrame({
        "time":    list(range(20)),
        "queries": np.random.randint(50, 100, 20),
        "co2":     np.random.randint(20, 50, 20),
        "power":   np.random.randint(250, 350, 20),
    })

_defaults = {
    "running":          False,
    "mode":             "normal",
    "data":             fresh_data(),
    "session_start":    datetime.now(),
    "cumulative_co2":   0.0,
    "cumulative_power": 0.0,
    "total_queries":    0,
    "chat_history":     [],
    "last_time":        pd.Timestamp.now(),
    "last_ai_summary":  "",
    "last_summary_ts":  0,
    # NEW state
    "alert_log":        [],       # list of {ts, level, message, co2, model}
    "session_snapshots":[],       # list of {ts, avg_co2, eff, queries}
    "peak_co2":         0.0,
    "peak_power":       0.0,
    "peak_queries":     0,
    "total_alerts":     0,
    "uptime_ticks":     0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v if not callable(v) else v()

# ================================================================
# UTILITY FUNCTIONS
# ================================================================
def get_status(avg_co2: float) -> tuple[str, str]:
    if avg_co2 > co2_critical: return "🔴 CRITICAL", THEME["red"]
    if avg_co2 > co2_high:     return "🟠 HIGH",     THEME["orange"]
    if avg_co2 > co2_medium:   return "🟡 MEDIUM",   THEME["yellow"]
    return "🟢 LOW", THEME["green"]


def efficiency_score(df: pd.DataFrame, mdl: str) -> float:
    spec = MODEL_SPECS[mdl]
    co2_per_q = df["co2"].mean() / max(df["queries"].mean(), 1)
    raw = 1 - (co2_per_q / 2.0)
    return round(max(0, min(100, raw * 100 * spec["efficiency"])), 1)


def trees_needed(co2_kg: float) -> float:
    return round(co2_kg / TREE_ABSORPTION_KG_YR, 2)


def linear_forecast(series: pd.Series, steps: int = 10) -> np.ndarray:
    y = series.values.astype(float)
    if len(y) < 3:
        return np.full(steps, y[-1])
    alpha, beta = 0.4, 0.2
    level, trend = y[0], y[1] - y[0]
    for v in y[1:]:
        prev_level = level
        level = alpha * v + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
    return np.array([level + i * trend for i in range(1, steps + 1)])


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
        if "content" in data:
            return data["content"][0]["text"]
        return f"API returned unexpected structure: {data.get('error', data)}"
    except requests.Timeout:
        return "⚠️ Request timed out. Try again."
    except Exception as e:
        return f"API error: {e}"


def export_pdf(df: pd.DataFrame) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AI Sustainability Report", styles["Title"]))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Paragraph(f"Model: {model}", styles["Normal"]))
        story.append(Spacer(1, 12))

        rows = [
            ["Metric", "Value"],
            ["Avg CO₂ (kg)",       round(df["co2"].mean(), 2)],
            ["Peak CO₂ (kg)",      int(df["co2"].max())],
            ["Avg Power (kWh)",    round(df["power"].mean(), 2)],
            ["Cumulative CO₂ (kg)",round(st.session_state.cumulative_co2, 2)],
            ["Trees Needed/yr",    trees_needed(st.session_state.cumulative_co2)],
            ["Efficiency Score",   f"{efficiency_score(df, model)}/100"],
            ["Carbon Cost ($)",    f"${round(st.session_state.cumulative_co2 * CARBON_PRICE_PER_KG, 2)}"],
            ["Total Alerts",       st.session_state.total_alerts],
            ["Peak CO₂ (kg)",      round(st.session_state.peak_co2, 2)],
            ["Total Queries",      st.session_state.total_queries],
        ]

        t = Table(rows, colWidths=[220, 180])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0c4a6e")),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f9ff")]),
        ]))
        story.append(t)

        # Add alert log summary
        story.append(Spacer(1, 20))
        story.append(Paragraph("Alert Log (last 10)", styles["Heading2"]))
        if st.session_state.alert_log:
            alert_rows = [["Time", "Level", "Message"]]
            for a in st.session_state.alert_log[-10:]:
                alert_rows.append([a.get("ts",""), a.get("level",""), a.get("message","")])
            at = Table(alert_rows, colWidths=[120, 80, 200])
            at.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
                ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID",        (0, 0), (-1, -1), 0.4, colors.lightgrey),
                ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ]))
            story.append(at)

        doc.build(story)
        buf.seek(0)
        return buf.read()
    except ImportError:
        return None


# ---- NEW: Log an alert event ----
def log_alert(level: str, message: str, co2: float):
    entry = {
        "ts":      datetime.now().strftime("%H:%M:%S"),
        "level":   level,
        "message": message,
        "co2":     co2,
        "model":   model,
    }
    st.session_state.alert_log.insert(0, entry)
    st.session_state.alert_log = st.session_state.alert_log[:200]  # cap at 200
    st.session_state.total_alerts += 1


# ---- NEW: Compute sustainability scorecard ----
def compute_scorecard(df: pd.DataFrame, mdl: str) -> dict:
    eff   = efficiency_score(df, mdl)
    avg   = df["co2"].mean()
    stdv  = df["co2"].std() if len(df) > 2 else 0

    # Stability: lower std relative to mean = better
    stability = max(0, min(100, 100 - (stdv / max(avg, 1)) * 100))

    # Carbon intensity: inverse of co2 per query
    co2_per_q = avg / max(df["queries"].mean(), 1)
    carbon_int = max(0, min(100, (1 - co2_per_q / 2.0) * 100))

    # Alert burden: penalise for alerts per tick
    ticks = max(st.session_state.uptime_ticks, 1)
    alert_rate = st.session_state.total_alerts / ticks
    alert_score = max(0, min(100, (1 - alert_rate * 10) * 100))

    overall = round((eff * 0.35 + stability * 0.25 + carbon_int * 0.25 + alert_score * 0.15), 1)

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


# ---- NEW: Cost projection calculations ----
def cost_projections(cum_co2: float, avg_co2_per_tick: float) -> dict:
    hourly_ticks = 3600 / SLEEP_INTERVAL  # approximate
    daily_co2    = avg_co2_per_tick * hourly_ticks * 24
    weekly_co2   = daily_co2 * 7
    monthly_co2  = daily_co2 * 30
    yearly_co2   = daily_co2 * 365

    return {
        "daily_co2":    round(daily_co2,   1),
        "weekly_co2":   round(weekly_co2,  1),
        "monthly_co2":  round(monthly_co2, 1),
        "yearly_co2":   round(yearly_co2,  1),
        "daily_cost":   round(daily_co2   * CARBON_PRICE_PER_KG, 2),
        "weekly_cost":  round(weekly_co2  * CARBON_PRICE_PER_KG, 2),
        "monthly_cost": round(monthly_co2 * CARBON_PRICE_PER_KG, 2),
        "yearly_cost":  round(yearly_co2  * CARBON_PRICE_PER_KG, 2),
        "trees_daily":  trees_needed(daily_co2),
        "trees_yearly": trees_needed(yearly_co2),
    }


# ================================================================
# HEADER
# ================================================================
elapsed = str(datetime.now() - st.session_state.session_start).split(".")[0]
mode_colors = {
    "normal": THEME["green"], "spike": THEME["red"],
    "low":    THEME["accent"], "high": THEME["orange"],
}
mode_color = mode_colors.get(st.session_state.mode, THEME["accent"])

# NEW: Live indicator pulse
live_pulse = f'<span class="pulse-dot" style="background:{THEME["green"]};"></span>' if st.session_state.running else f'<span style="width:8px;height:8px;border-radius:50%;background:{THEME["muted"]};display:inline-block;"></span>'

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;
            padding-bottom:12px;border-bottom:1px solid {THEME['border']};margin-bottom:16px;">
  <div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                letter-spacing:.12em;text-transform:uppercase;color:{THEME['muted']};
                margin-bottom:4px;">AI Sustainability Monitor · v4</div>
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
    <div>Mode:
      <span style="color:{mode_color};font-weight:600;
                   text-transform:uppercase;">{st.session_state.mode}</span>
    </div>
    <div>Alerts: <span style="color:{THEME['red'] if st.session_state.total_alerts > 5 else THEME['text']};">{st.session_state.total_alerts}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ================================================================
# METRICS ROW
# ================================================================
df = st.session_state.data
latest      = df.iloc[-1]
avg_co2_now = df["co2"].tail(5).mean()
status_label, _ = get_status(avg_co2_now)
eff         = efficiency_score(df, model)
carbon_cost = st.session_state.cumulative_co2 * CARBON_PRICE_PER_KG
trees       = trees_needed(st.session_state.cumulative_co2)

delta_co2   = int(df["co2"].iloc[-1]    - df["co2"].iloc[-2])    if len(df) > 1 else 0
delta_q     = int(df["queries"].iloc[-1] - df["queries"].iloc[-2]) if len(df) > 1 else 0
delta_power = int(df["power"].iloc[-1]  - df["power"].iloc[-2])  if len(df) > 1 else 0

row1 = st.columns(6)
row1[0].metric("Queries / tick",    int(latest["queries"]),  delta=delta_q)
row1[1].metric("CO₂ (kg)",          int(latest["co2"]),      delta=delta_co2,   delta_color="inverse")
row1[2].metric("Power (kWh)",       int(latest["power"]),    delta=delta_power, delta_color="inverse")
row1[3].metric("System Status",     status_label)
row1[4].metric("Efficiency",        f"{eff}/100")
row1[5].metric("Carbon Cost",       f"${carbon_cost:.2f}")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

row2 = st.columns(5)
row2[0].metric("🌳 Trees Needed / yr",   str(trees))
row2[1].metric("📦 Cumul. CO₂ (kg)",     round(st.session_state.cumulative_co2, 2))
row2[2].metric("⚡ Cumul. Power (kWh)",  round(st.session_state.cumulative_power, 2))
row2[3].metric("🏔️ Peak CO₂ (kg)",       round(st.session_state.peak_co2, 2))
row2[4].metric("🔔 Total Alerts",        st.session_state.total_alerts)

# ================================================================
# CONTROLS
# ================================================================
st.markdown("<hr>", unsafe_allow_html=True)

ctl_left, ctl_right = st.columns([1, 1])

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
            for k, v in _defaults.items():
                st.session_state[k] = v if not callable(v) else v()
            st.session_state["data"] = fresh_data()
            st.rerun()

with ctl_right:
    st.markdown('<div class="section-pill">System Behavior</div>', unsafe_allow_html=True)
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("⚠️ Spike",  use_container_width=True):
            st.session_state.mode = "spike"
            log_alert("HIGH", f"Manual spike mode activated on {model}", latest["co2"])
    with b2:
        if st.button("📉 Reduce", use_container_width=True): st.session_state.mode = "low"
    with b3:
        if st.button("🚀 Boost",  use_container_width=True):
            st.session_state.mode = "high"
            log_alert("MEDIUM", f"Boost mode activated — increased load expected", latest["co2"])
    with b4:
        if st.button("✅ Normal", use_container_width=True): st.session_state.mode = "normal"

st.markdown("<hr>", unsafe_allow_html=True)

# ================================================================
# TABS — now 7 tabs
# ================================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⚡ Real-Time",
    "📊 Analytics",
    "📈 Advanced",
    "🧠 AI Insights",
    "🤖 Model Compare",
    "🚨 Alert Log",          # NEW
    "🎯 Score & Projections", # NEW
])

# ──────────────────────────────────────────────
# TAB 1 · REAL-TIME
# ──────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-pill">Live System Monitoring</div>', unsafe_allow_html=True)

    chart_ph      = st.empty()
    status_ph     = st.empty()
    data_table_ph = st.empty()

    spec = MODEL_SPECS[model]

    def _render_live_chart(df_: pd.DataFrame, forecast_times, forecast_vals,
                           anomalies_: pd.DataFrame, sl: str) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_["time"], y=df_["co2"],
            name="CO₂ (kg)", mode="lines",
            line=dict(width=2.5, color=THEME["red"]),
            fill="tozeroy", fillcolor="rgba(248,113,113,0.07)"
        ))
        fig.add_trace(go.Scatter(
            x=df_["time"], y=df_["queries"],
            name="Queries", mode="lines",
            line=dict(color=THEME["accent"], width=1.8)
        ))
        fig.add_trace(go.Scatter(
            x=df_["time"], y=df_["power"],
            name="Power (kWh)", mode="lines",
            line=dict(color=THEME["green"], width=1.8)
        ))
        if show_forecast:
            fig.add_trace(go.Scatter(
                x=forecast_times, y=forecast_vals,
                name="CO₂ Forecast", mode="lines",
                line=dict(color=THEME["orange"], dash="dot", width=2)
            ))
            # NEW: Forecast confidence band
            upper = forecast_vals * 1.1
            lower = forecast_vals * 0.9
            fig.add_trace(go.Scatter(
                x=list(forecast_times) + list(forecast_times)[::-1],
                y=list(upper) + list(lower)[::-1],
                fill="toself", fillcolor="rgba(251,146,60,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                name="Forecast Band", showlegend=False
            ))
        if show_anomalies and not anomalies_.empty:
            fig.add_trace(go.Scatter(
                x=anomalies_["time"], y=anomalies_["co2"],
                mode="markers", name="Anomaly",
                marker=dict(size=10, color=THEME["red"], symbol="x",
                            line=dict(width=2, color="#fff"))
            ))
        if show_thresholds:
            fig.add_hrect(y0=0,            y1=co2_medium,   fillcolor=THEME["green"],  opacity=0.06)
            fig.add_hrect(y0=co2_medium,   y1=co2_high,     fillcolor=THEME["yellow"], opacity=0.06)
            fig.add_hrect(y0=co2_high,     y1=co2_critical, fillcolor=THEME["orange"], opacity=0.06)
            fig.add_hrect(y0=co2_critical, y1=200,          fillcolor=THEME["red"],    opacity=0.06)
        fig.update_layout(
            height=420, template=THEME["plotly"],
            title=dict(text=f"Live Monitor  ·  {sl}  ·  {model}",
                       font=dict(family="IBM Plex Mono", size=13)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        font=dict(family="IBM Plex Mono", size=11)),
            margin=dict(l=10, r=10, t=50, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor=THEME["border"]),
            yaxis=dict(showgrid=True, gridcolor=THEME["border"]),
        )
        return fig

    if st.session_state.running:
        for _ in range(MAX_SIM_ITERATIONS):
            now  = st.session_state.last_time + pd.Timedelta(seconds=1)
            st.session_state.last_time = now

            mode = st.session_state.mode
            prev = st.session_state.data.iloc[-1]

            base_q = prev["queries"] + np.random.randint(-10, 10)
            if mode == "spike":
                base_q += np.random.randint(40, 80) * intensity
            elif mode == "low":
                base_q -= np.random.randint(20, 40)
            elif mode == "high":
                base_q += np.random.randint(20, 50) * intensity

            queries = int(np.clip(base_q, 10, 220))
            co2     = int(np.clip(queries * spec["base_co2"] * (1 + np.random.uniform(-0.1, 0.2)), 5, 150))
            power   = int(np.clip(queries * spec["base_power"] * (1 + np.random.uniform(-0.05, 0.15)), 80, 600))

            st.session_state.cumulative_co2   += co2
            st.session_state.cumulative_power += power
            st.session_state.total_queries    += queries
            st.session_state.uptime_ticks     += 1

            # NEW: Update peak tracking
            if co2 > st.session_state.peak_co2:
                st.session_state.peak_co2 = co2
            if power > st.session_state.peak_power:
                st.session_state.peak_power = power
            if queries > st.session_state.peak_queries:
                st.session_state.peak_queries = queries

            new_row = {"time": now, "queries": queries, "co2": co2, "power": power}
            st.session_state.data = pd.concat(
                [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
            ).tail(window)

            df_ = st.session_state.data.copy()
            avg_co2_ = df_["co2"].tail(5).mean()
            sl, sc = get_status(avg_co2_)

            # NEW: Threshold-triggered alert logging
            if co2 > co2_critical:
                log_alert("CRITICAL", f"CO₂ exceeded critical threshold: {co2}kg on {model}", co2)
            elif co2 > co2_high and np.random.random() < 0.15:  # throttle medium alerts
                log_alert("HIGH", f"CO₂ above high threshold: {co2}kg", co2)

            # NEW: Snapshot for scorecard history
            if st.session_state.uptime_ticks % 10 == 0:
                st.session_state.session_snapshots.append({
                    "tick":    st.session_state.uptime_ticks,
                    "avg_co2": round(df_["co2"].mean(), 1),
                    "eff":     efficiency_score(df_, model),
                    "queries": int(df_["queries"].mean()),
                })
                st.session_state.session_snapshots = st.session_state.session_snapshots[-50:]

            status_ph.markdown(
                f'<div class="status-badge" style="background:rgba(0,0,0,.3);'
                f'border:1px solid {sc};">'
                f'<span style="color:{sc};font-size:16px;">●</span>'
                f'<span style="color:{THEME["text"]};">System Status: </span>'
                f'<span style="color:{sc};">{sl}</span></div>',
                unsafe_allow_html=True
            )

            rolling_mean = df_["co2"].rolling(5).mean().fillna(df_["co2"])
            rolling_std  = df_["co2"].rolling(5).std().fillna(0)
            anomalies_   = df_[df_["co2"] > (rolling_mean + 2 * rolling_std)]

            forecast_vals  = linear_forecast(df_["co2"], steps=8)
            last_t = df_["time"].iloc[-1]
            try:
                forecast_times = [last_t + pd.Timedelta(seconds=i+1) for i in range(8)]
            except Exception:
                forecast_times = list(range(len(df_), len(df_)+8))

            chart_ph.plotly_chart(
                _render_live_chart(df_, forecast_times, forecast_vals, anomalies_, sl),
                use_container_width=True
            )

            styled = df_.tail(10).style.applymap(
                lambda x: f"color:{THEME['red']};font-weight:600"
                if isinstance(x, (int, float)) and x > co2_high else ""
            )
            data_table_ph.dataframe(styled, use_container_width=True, height=240)

            co2_changed = abs(co2 - getattr(st.session_state, "_last_co2_for_summary", co2)) > 10
            time_elapsed = time.time() - st.session_state.last_summary_ts > AI_SUMMARY_INTERVAL
            if ANTHROPIC_API_KEY and time_elapsed and co2_changed:
                st.session_state._last_co2_for_summary = co2
                prompt = (
                    f"Metrics — CO₂: {co2}kg, Queries: {queries}, Power: {power}kWh, "
                    f"Model: {model}, Mode: {mode}. 2-sentence sustainability insight."
                )
                st.session_state.last_ai_summary = call_claude(prompt)
                st.session_state.last_summary_ts = time.time()

            time.sleep(SLEEP_INTERVAL)
            if not st.session_state.running:
                break

    # Static render when stopped
    df_ = st.session_state.data.copy()
    if not df_.empty:
        avg_co2_ = df_["co2"].tail(5).mean()
        sl, sc   = get_status(avg_co2_)
        status_ph.markdown(
            f'<div class="status-badge" style="background:rgba(0,0,0,.3);'
            f'border:1px solid {sc};">'
            f'<span style="color:{sc};font-size:16px;">●</span>'
            f'<span style="color:{THEME["text"]};">System Status: </span>'
            f'<span style="color:{sc};">{sl}</span></div>',
            unsafe_allow_html=True
        )
        forecast_vals  = linear_forecast(df_["co2"], steps=8)
        last_t = df_["time"].iloc[-1]
        try:
            forecast_times = [last_t + pd.Timedelta(seconds=i+1) for i in range(8)]
        except Exception:
            forecast_times = list(range(len(df_), len(df_)+8))
        chart_ph.plotly_chart(
            _render_live_chart(df_, forecast_times, forecast_vals, pd.DataFrame(), sl),
            use_container_width=True
        )
        data_table_ph.dataframe(df_.tail(10), use_container_width=True, height=240)

    if st.session_state.last_ai_summary:
        st.info(f"🤖 **Auto AI Summary:** {st.session_state.last_ai_summary}")

# ──────────────────────────────────────────────
# TAB 2 · ANALYTICS
# ──────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-pill">System Analytics</div>', unsafe_allow_html=True)
    df = st.session_state.data

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg CO₂",    round(df["co2"].mean(), 2))
    m2.metric("Peak CO₂",   int(df["co2"].max()))
    m3.metric("Avg Power",  round(df["power"].mean(), 2))
    m4.metric("Efficiency", f"{efficiency_score(df, model)}/100")

    st.markdown("### 📈 Smoothed Trends")
    rolling = df.set_index("time").rolling(5).mean()
    fig_trends = go.Figure()
    for col, color in [("co2", THEME["red"]), ("queries", THEME["accent"]), ("power", THEME["green"])]:
        fig_trends.add_trace(go.Scatter(
            x=rolling.index, y=rolling[col], name=col.capitalize(),
            mode="lines", line=dict(color=color, width=2)
        ))
    fig_trends.update_layout(
        template=THEME["plotly"], height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(font=dict(family="IBM Plex Mono", size=11)),
        xaxis=dict(gridcolor=THEME["border"]),
        yaxis=dict(gridcolor=THEME["border"]),
    )
    st.plotly_chart(fig_trends, use_container_width=True)

    # NEW: Distribution histogram
    st.markdown("### 📊 CO₂ Distribution")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=df["co2"], nbinsx=20,
        marker_color=THEME["accent"],
        opacity=0.75, name="CO₂ Distribution"
    ))
    fig_hist.add_vline(x=df["co2"].mean(), line_color=THEME["green"],
                        line_dash="dash", annotation_text="Mean",
                        annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_hist.add_vline(x=co2_critical, line_color=THEME["red"],
                        line_dash="dot", annotation_text="Critical",
                        annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_hist.update_layout(
        template=THEME["plotly"], height=280,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="CO₂ (kg)", yaxis_title="Frequency",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("### 🔮 CO₂ Forecast  ·  Next 10 Cycles  (Holt's Smoothing)")
    forecast_vals = linear_forecast(df["co2"], steps=10)
    last_idx = len(df)
    fig_fc = go.Figure()
    fig_fc.add_trace(go.Scatter(
        y=df["co2"].values, name="Historical CO₂",
        line=dict(color=THEME["red"], width=2)
    ))
    fig_fc.add_trace(go.Scatter(
        x=list(range(last_idx, last_idx+10)), y=forecast_vals,
        name="Forecast", mode="lines+markers",
        line=dict(color=THEME["orange"], dash="dot", width=2),
        marker=dict(size=5)
    ))
    fig_fc.update_layout(
        template=THEME["plotly"], height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_fc, use_container_width=True)

    st.markdown("### 🔗 Feature Correlation")
    corr = df[["queries", "co2", "power"]].corr()
    fig_corr = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale="RdBu", zmid=0,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}", textfont=dict(family="IBM Plex Mono", size=13)
    ))
    fig_corr.update_layout(template=THEME["plotly"], height=280,
                            paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=10,r=10,t=10,b=10))
    st.plotly_chart(fig_corr, use_container_width=True)

    cum_co2 = st.session_state.cumulative_co2
    st.info(
        f"**Session CO₂: {round(cum_co2, 1)} kg** — "
        f"requires **{trees_needed(cum_co2)} trees/year** to offset. "
        f"Carbon cost at ${CARBON_PRICE_PER_KG}/kg: **${round(cum_co2 * CARBON_PRICE_PER_KG, 2)}**"
    )

# ──────────────────────────────────────────────
# TAB 3 · ADVANCED
# ──────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-pill">Advanced Insights</div>', unsafe_allow_html=True)
    df = st.session_state.data.copy()

    for col in ["queries", "co2", "power"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().reset_index(drop=True)
    df["index"] = df.index

    if len(df) < 8:
        st.warning("⚠️ Start the simulation to generate enough data for advanced visualizations.")
    else:
        df_sample = df.iloc[::max(1, len(df)//60)]

        st.markdown("### 🌐 3D System View")
        fig3d = px.scatter_3d(
            df_sample, x="index", y="queries", z="co2",
            color="power", size="queries",
            color_continuous_scale="Turbo",
            opacity=0.85,
        )
        fig3d.update_traces(marker=dict(size=5))
        fig3d.update_layout(
            template=THEME["plotly"], height=460,
            scene=dict(
                xaxis_title="Time", yaxis_title="Queries", zaxis_title="CO₂",
                bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor=THEME["border"]),
                yaxis=dict(gridcolor=THEME["border"]),
                zaxis=dict(gridcolor=THEME["border"]),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig3d, use_container_width=True)

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("### 🔵 Load vs Emissions")
            fig_b = px.scatter(
                df, x="queries", y="co2", size="power", color="power",
                color_continuous_scale="Turbo",
                labels={"queries": "Query Load", "co2": "CO₂ (kg)"},
            )
            fig_b.update_layout(template=THEME["plotly"], height=340,
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(l=10,r=10,t=20,b=10))
            st.plotly_chart(fig_b, use_container_width=True)

        with col_r:
            st.markdown("### ⚡ CO₂ Stress Gauge")
            stress = int(min(120, df["co2"].iloc[-1]))
            gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=stress,
                delta={"reference": int(df["co2"].mean()), "increasing": {"color": THEME["red"]}},
                title={"text": "CO₂ Stress Level", "font": {"family": "IBM Plex Mono", "size": 14}},
                number={"font": {"family": "IBM Plex Mono"}},
                gauge={
                    "axis":  {"range": [0, 120], "tickfont": {"family": "IBM Plex Mono", "size": 10}},
                    "bar":   {"color": THEME["red"]},
                    "steps": [
                        {"range": [0,            co2_medium],   "color": "rgba(52,211,153,.25)"},
                        {"range": [co2_medium,   co2_high],     "color": "rgba(251,191,36,.25)"},
                        {"range": [co2_high,     co2_critical], "color": "rgba(251,146,60,.25)"},
                        {"range": [co2_critical, 120],          "color": "rgba(248,113,113,.25)"},
                    ],
                    "threshold": {
                        "line": {"color": THEME["orange"], "width": 3},
                        "thickness": 0.75, "value": co2_critical,
                    },
                }
            ))
            gauge.update_layout(height=340, template=THEME["plotly"],
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  margin=dict(l=20, r=20, t=30, b=10))
            st.plotly_chart(gauge, use_container_width=True)

        # NEW: Power efficiency over time
        st.markdown("### 🔋 Power Efficiency Trend")
        df["co2_per_query"] = df["co2"] / df["queries"].replace(0, 1)
        df["power_per_query"] = df["power"] / df["queries"].replace(0, 1)
        fig_eff_t = go.Figure()
        fig_eff_t.add_trace(go.Scatter(
            x=df["index"], y=df["co2_per_query"].rolling(5).mean(),
            name="CO₂/Query", mode="lines",
            line=dict(color=THEME["red"], width=2)
        ))
        fig_eff_t.add_trace(go.Scatter(
            x=df["index"], y=df["power_per_query"].rolling(5).mean(),
            name="Power/Query", mode="lines",
            line=dict(color=THEME["purple"], width=2)
        ))
        fig_eff_t.update_layout(
            template=THEME["plotly"], height=260,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(font=dict(family="IBM Plex Mono", size=11)),
        )
        st.plotly_chart(fig_eff_t, use_container_width=True)

        st.markdown("### 🚨 Anomaly Detection")
        rolling_mean = df["co2"].rolling(5).mean().fillna(df["co2"])
        rolling_std  = df["co2"].rolling(5).std().fillna(0)
        anomalies    = df[df["co2"] > (rolling_mean + 1.5 * rolling_std)]

        a_left, a_right = st.columns([1, 3])
        with a_left:
            st.metric("Anomalies Detected", len(anomalies))
            pct = round(len(anomalies) / len(df) * 100, 1)
            st.metric("Anomaly Rate", f"{pct}%")

        with a_right:
            if not anomalies.empty:
                fig_anom = px.bar(
                    anomalies, x="index", y="co2", color="co2",
                    color_continuous_scale="Reds",
                    labels={"index": "Tick", "co2": "CO₂ (kg)"}
                )
                fig_anom.update_layout(template=THEME["plotly"], height=260,
                                        paper_bgcolor="rgba(0,0,0,0)",
                                        plot_bgcolor="rgba(0,0,0,0)",
                                        margin=dict(l=10,r=10,t=10,b=10),
                                        showlegend=False)
                st.plotly_chart(fig_anom, use_container_width=True)
            else:
                st.success("No anomalies detected in current window.")

# ──────────────────────────────────────────────
# TAB 4 · AI INSIGHTS
# ──────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-pill">AI Decision Engine</div>', unsafe_allow_html=True)

    df        = st.session_state.data
    latest    = df.iloc[-1]
    co2_v     = latest["co2"]
    queries_v = latest["queries"]
    power_v   = latest["power"]

    if co2_v > co2_critical:
        st.error("🚨 **Critical System State** — Immediate action required")
        risk = "HIGH"
    elif co2_v > co2_medium:
        st.warning("⚠️ **Moderate Risk** — Monitor and optimize")
        risk = "MEDIUM"
    else:
        st.success("✅ **Healthy System** — Operating within acceptable thresholds")
        risk = "LOW"

    trend = df["co2"].tail(5).mean() - df["co2"].head(5).mean()
    if trend > 10:
        st.warning("📈 **CO₂ Trend:** Increasing — intervention may be needed")
    elif trend < -10:
        st.success("📉 **CO₂ Trend:** Decreasing — optimizations are working")
    else:
        st.info("➡️ **CO₂ Trend:** Stable")

    forecast_next = int(linear_forecast(df["co2"], steps=1)[0])
    fi_left, fi_right = st.columns(2)
    fi_left.metric("🔮 Predicted CO₂ (Next Cycle)", f"{forecast_next} kg",
                   delta=forecast_next - int(co2_v), delta_color="inverse")
    fi_right.metric("📊 Risk Level", risk)

    st.markdown("### 🤖 Recommendations")
    if risk == "HIGH":
        recs = [
            "Shift workloads to off-peak hours to take advantage of lower-carbon grid periods",
            "Enable model compression / quantization to reduce per-query footprint",
            "Reduce concurrent query load immediately — consider request queuing",
            f"Switch to a lighter model (e.g. **Sonar** at 0.22 kg CO₂/query vs {MODEL_SPECS[model]['base_co2']} kg)",
        ]
    elif risk == "MEDIUM":
        recs = [
            "Optimize request batching to reduce per-query overhead",
            "Review query routing policies — eliminate redundant model calls",
            "Monitor energy usage; schedule heavy workloads during renewable-heavy grid windows",
        ]
    else:
        recs = [
            "Maintain current configuration — system is healthy",
            "Continue monitoring for drift in query patterns",
            "Explore further efficiency gains with caching or prompt compression",
        ]
    for i, r in enumerate(recs, 1):
        st.markdown(f"**{i}.** {r}")

    st.markdown("### 🧪 Scenario Simulation")
    sc_col1, sc_col2 = st.columns([1, 2])
    with sc_col1:
        scenario = st.selectbox("Choose Scenario", ["Peak Load", "Optimized", "Balanced"])
    with sc_col2:
        scenarios = {
            "Peak Load":  (THEME["red"],    "High CO₂ spike expected. Stress gauge will enter critical zone."),
            "Optimized":  (THEME["green"],  "Reduced emissions. Efficiency score improves significantly."),
            "Balanced":   (THEME["accent"], "Moderate load. Stable emissions and predictable performance."),
        }
        color, msg = scenarios[scenario]
        st.markdown(
            f'<div style="background:rgba(0,0,0,.2);border:1px solid {color};'
            f'border-radius:8px;padding:10px 14px;font-family:IBM Plex Mono,monospace;'
            f'font-size:13px;color:{color};">{msg}</div>',
            unsafe_allow_html=True
        )

    # NEW: Efficiency benchmark comparison
    st.markdown("### 📐 Model Efficiency Benchmark")
    curr_co2_per_q = df["co2"].mean() / max(df["queries"].mean(), 1)
    bench_data = []
    for m_name, m_spec in MODEL_SPECS.items():
        bench_data.append({
            "Model": m_name,
            "CO₂/Query": round(m_spec["base_co2"], 3),
            "Selected": m_name == model
        })
    bench_df = pd.DataFrame(bench_data)
    fig_bench = px.bar(
        bench_df, x="Model", y="CO₂/Query",
        color="CO₂/Query", color_continuous_scale="RdYlGn_r",
        text="CO₂/Query"
    )
    fig_bench.add_hline(y=curr_co2_per_q, line_color=THEME["purple"],
                         line_dash="dash",
                         annotation_text=f"Current avg: {curr_co2_per_q:.3f}",
                         annotation_font=dict(family="IBM Plex Mono", size=11))
    fig_bench.update_traces(textposition="outside", textfont=dict(family="IBM Plex Mono", size=10))
    fig_bench.update_layout(
        template=THEME["plotly"], height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_bench, use_container_width=True)

    st.markdown("### 💬 Ask the AI Sustainability Expert")

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-user"><strong>You</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-ai"><strong>🤖 AI</strong><br>{msg["content"]}</div>',
                    unsafe_allow_html=True
                )

    query = st.text_area(
        "Your question",
        placeholder="e.g. How can I reduce CO₂ for this model at peak load?",
        label_visibility="collapsed",
        height=90,
    )

    q_col1, q_col2 = st.columns([3, 1])
    with q_col1:
        run_btn = st.button("🚀 Analyze", use_container_width=True)
    with q_col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if run_btn and query.strip():
        prompt = (
            f"System metrics — CO₂: {co2_v}kg, Queries: {queries_v}, Power: {power_v}kWh, "
            f"Model: {model}, Risk: {risk}, "
            f"Trend: {'increasing' if trend > 10 else 'decreasing' if trend < -10 else 'stable'}, "
            f"Cumulative CO₂: {round(st.session_state.cumulative_co2,1)}kg. "
            f"User question: {query}"
        )
        with st.spinner("Analyzing…"):
            response = call_claude(prompt)
        st.session_state.chat_history.append({"role": "user",      "content": query})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

# ──────────────────────────────────────────────
# TAB 5 · MODEL COMPARE
# ──────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-pill">Model Comparison</div>', unsafe_allow_html=True)

    avg_q = int(st.session_state.data["queries"].mean())
    st.caption(f"Estimates based on current average query load: **{avg_q} queries/tick**")

    rows = []
    for m, spec in MODEL_SPECS.items():
        rows.append({
            "Model":            m,
            "Est. CO₂ (kg)":    round(avg_q * spec["base_co2"],    1),
            "Est. Power (kWh)": round(avg_q * spec["base_power"],  1),
            "Efficiency (%)":   round(spec["efficiency"] * 100,    1),
            "Carbon Cost ($)":  round(avg_q * spec["base_co2"] * CARBON_PRICE_PER_KG, 2),
        })
    compare_df = pd.DataFrame(rows).sort_values("Est. CO₂ (kg)")

    def _highlight(row):
        if row["Model"] == model:
            return [f"background-color:rgba(56,189,248,.12);color:{THEME['accent']};font-weight:600"] * len(row)
        return [""] * len(row)

    st.dataframe(compare_df.style.apply(_highlight, axis=1), use_container_width=True, height=260)

    mc1, mc2 = st.columns(2)
    with mc1:
        fig_co2 = px.bar(
            compare_df, x="Model", y="Est. CO₂ (kg)",
            color="Efficiency (%)", color_continuous_scale="RdYlGn",
            text="Est. CO₂ (kg)", title="CO₂ Emissions by Model",
        )
        fig_co2.update_traces(textposition="outside", textfont=dict(family="IBM Plex Mono", size=11))
        fig_co2.update_layout(
            template=THEME["plotly"], height=380,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=40, b=10),
            title_font=dict(family="IBM Plex Mono", size=13),
        )
        st.plotly_chart(fig_co2, use_container_width=True)

    with mc2:
        fig_eff = px.bar(
            compare_df, x="Model", y="Efficiency (%)",
            color="Efficiency (%)", color_continuous_scale="Blues",
            text="Efficiency (%)", title="Efficiency Score by Model",
        )
        fig_eff.update_traces(textposition="outside", textfont=dict(family="IBM Plex Mono", size=11))
        fig_eff.update_layout(
            template=THEME["plotly"], height=380,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=40, b=10),
            title_font=dict(family="IBM Plex Mono", size=13),
        )
        st.plotly_chart(fig_eff, use_container_width=True)

    # NEW: Radar chart for model comparison
    st.markdown("### 🕸️ Multi-Dimensional Model Radar")
    categories = ["Efficiency", "Low CO₂", "Low Power", "Cost Efficiency"]
    fig_radar = go.Figure()
    for m_name, m_spec in MODEL_SPECS.items():
        norm_eff   = m_spec["efficiency"] * 100
        norm_co2   = (1 - m_spec["base_co2"] / 0.60) * 100
        norm_power = (1 - m_spec["base_power"] / 3.0) * 100
        norm_cost  = norm_co2  # cost tracks co2 directly
        vals = [norm_eff, norm_co2, norm_power, norm_cost, norm_eff]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals,
            theta=categories + [categories[0]],
            fill="toself",
            name=m_name,
            opacity=0.7 if m_name == model else 0.35,
            line=dict(width=2.5 if m_name == model else 1),
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        template=THEME["plotly"], height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(family="IBM Plex Mono", size=11)),
        margin=dict(l=30, r=30, t=30, b=30),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    best  = compare_df.iloc[0]["Model"]
    worst = compare_df.iloc[-1]["Model"]
    st.success(f"✅ Most efficient at current load: **{best}**")
    if model == worst:
        st.warning(f"⚠️ You are using **{model}**, which has the highest estimated CO₂. "
                   f"Consider switching to **{best}** for a "
                   f"{round((1 - MODEL_SPECS[best]['base_co2']/MODEL_SPECS[model]['base_co2'])*100)}% reduction.")

# ──────────────────────────────────────────────
# TAB 6 · ALERT LOG  (NEW)
# ──────────────────────────────────────────────
with tab6:
    st.markdown('<div class="section-pill">Alert History & Event Log</div>', unsafe_allow_html=True)

    alert_log = st.session_state.alert_log

    # Summary metrics
    a1, a2, a3, a4 = st.columns(4)
    total = len(alert_log)
    critical_c = sum(1 for a in alert_log if a.get("level") == "CRITICAL")
    high_c     = sum(1 for a in alert_log if a.get("level") == "HIGH")
    medium_c   = sum(1 for a in alert_log if a.get("level") == "MEDIUM")
    a1.metric("Total Events",    total)
    a2.metric("🔴 Critical",     critical_c)
    a3.metric("🟠 High",         high_c)
    a4.metric("🟡 Medium / Info", medium_c)

    # Filter controls
    st.markdown("---")
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        level_filter = st.selectbox("Filter by Level", ["All", "CRITICAL", "HIGH", "MEDIUM"])
    with fc2:
        model_filter = st.selectbox("Filter by Model", ["All"] + list(MODEL_SPECS.keys()))
    with fc3:
        if st.button("🗑️ Clear Log", use_container_width=True):
            st.session_state.alert_log = []
            st.session_state.total_alerts = 0
            st.rerun()

    filtered = alert_log
    if level_filter != "All":
        filtered = [a for a in filtered if a.get("level") == level_filter]
    if model_filter != "All":
        filtered = [a for a in filtered if a.get("model") == model_filter]

    st.markdown(f"<div class='info-tooltip'>Showing {len(filtered)} of {total} events</div>",
                unsafe_allow_html=True)

    # Alert entries
    level_cfg = {
        "CRITICAL": (THEME["red"],    "🔴"),
        "HIGH":     (THEME["orange"], "🟠"),
        "MEDIUM":   (THEME["yellow"], "🟡"),
        "LOW":      (THEME["green"],  "🟢"),
    }

    if not filtered:
        st.info("No events logged yet. Start the simulation to generate alerts.")
    else:
        for entry in filtered[:50]:  # show latest 50
            lvl   = entry.get("level", "INFO")
            color, icon = level_cfg.get(lvl, (THEME["muted"], "ℹ️"))
            st.markdown(f"""
            <div class="alert-entry">
              <div class="alert-dot" style="background:{color};"></div>
              <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <span style="color:{color};font-weight:600;">{icon} {lvl}</span>
                  <span class="alert-time">{entry.get('ts','')}</span>
                </div>
                <div class="alert-msg">{entry.get('message','')}</div>
                <div class="alert-time" style="margin-top:3px;">
                  CO₂: {entry.get('co2','—')} kg &nbsp;·&nbsp; Model: {entry.get('model','—')}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Alert frequency chart
    if len(alert_log) >= 3:
        st.markdown("### 📊 Alert Frequency")
        al_df = pd.DataFrame(alert_log)
        al_counts = al_df.groupby("level").size().reset_index(name="count")
        fig_al = px.pie(
            al_counts, names="level", values="count",
            color="level",
            color_discrete_map={
                "CRITICAL": THEME["red"],
                "HIGH":     THEME["orange"],
                "MEDIUM":   THEME["yellow"],
            },
            hole=0.45,
        )
        fig_al.update_layout(
            template=THEME["plotly"], height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(font=dict(family="IBM Plex Mono", size=11)),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_al, use_container_width=True)

    # Export alert log
    if alert_log:
        al_export = pd.DataFrame(alert_log).to_csv(index=False).encode()
        st.download_button(
            "📁 Export Alert Log CSV",
            al_export,
            "alert_log.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ──────────────────────────────────────────────
# TAB 7 · SCORE & PROJECTIONS  (NEW)
# ──────────────────────────────────────────────
with tab7:
    st.markdown('<div class="section-pill">Sustainability Scorecard & Cost Projections</div>',
                unsafe_allow_html=True)

    df = st.session_state.data

    # ---- Scorecard ----
    st.markdown("### 🎯 Sustainability Scorecard")
    sc = compute_scorecard(df, model)

    def _score_card(label: str, value: float, detail: str):
        color = score_color(value)
        bar_w = int(value)
        return f"""
        <div class="score-ring">
          <div class="score-value" style="color:{color};">{value}</div>
          <div class="score-label">{label}</div>
          <div class="custom-progress">
            <div class="custom-progress-fill" style="width:{bar_w}%;background:{color};"></div>
          </div>
          <div class="score-sub">{detail}</div>
        </div>
        """

    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    sc1.markdown(_score_card("Overall", sc["overall"], "Composite score"), unsafe_allow_html=True)
    sc2.markdown(_score_card("Efficiency", sc["efficiency"], "CO₂ per query"), unsafe_allow_html=True)
    sc3.markdown(_score_card("Stability", sc["stability"], "Variance control"), unsafe_allow_html=True)
    sc4.markdown(_score_card("Carbon Int.", sc["carbon_int"], "Intensity rating"), unsafe_allow_html=True)
    sc5.markdown(_score_card("Alert Health", sc["alert"], "Alert burden"), unsafe_allow_html=True)

    # Grade
    overall = sc["overall"]
    grade = "A+" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 70 else "C" if overall >= 60 else "D" if overall >= 50 else "F"
    grade_color = score_color(overall)
    st.markdown(f"""
    <div style="text-align:center;padding:20px;background:var(--card);
                border:2px solid {grade_color};border-radius:12px;margin:12px 0;">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                  letter-spacing:.15em;text-transform:uppercase;color:var(--muted);">
        Sustainability Grade
      </div>
      <div style="font-family:'IBM Plex Mono',monospace;font-size:4rem;
                  font-weight:700;color:{grade_color};line-height:1.1;">{grade}</div>
      <div style="font-size:13px;color:var(--muted);">
        {model} · {datetime.now().strftime('%Y-%m-%d %H:%M')}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Scorecard history chart
    if st.session_state.session_snapshots:
        st.markdown("### 📈 Score History Over Session")
        snap_df = pd.DataFrame(st.session_state.session_snapshots)
        fig_snap = go.Figure()
        fig_snap.add_trace(go.Scatter(
            x=snap_df["tick"], y=snap_df["eff"],
            name="Efficiency", mode="lines+markers",
            line=dict(color=THEME["green"], width=2),
            marker=dict(size=5),
        ))
        fig_snap.add_trace(go.Scatter(
            x=snap_df["tick"], y=snap_df["avg_co2"],
            name="Avg CO₂", mode="lines+markers",
            line=dict(color=THEME["red"], width=2),
            marker=dict(size=5),
            yaxis="y2",
        ))
        fig_snap.update_layout(
            template=THEME["plotly"], height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=60, t=20, b=10),
            legend=dict(font=dict(family="IBM Plex Mono", size=11)),
            yaxis=dict(title="Efficiency Score", gridcolor=THEME["border"]),
            yaxis2=dict(title="Avg CO₂ (kg)", overlaying="y", side="right",
                        gridcolor=THEME["border"]),
        )
        st.plotly_chart(fig_snap, use_container_width=True)

    # ---- Cost Projections ----
    st.markdown("---")
    st.markdown("### 💰 Cost & Carbon Projections")

    avg_co2_tick = df["co2"].mean()
    proj = cost_projections(st.session_state.cumulative_co2, avg_co2_tick)

    p1, p2, p3, p4 = st.columns(4)

    def _proj_card(title, co2, cost, trees_val, color=THEME["accent"]):
        return f"""
        <div class="proj-card" style="border-left-color:{color};">
          <div class="proj-title">{title}</div>
          <div class="proj-value">${cost}</div>
          <div class="proj-detail">
            📦 {co2} kg CO₂<br>
            🌳 {trees_val} trees/yr to offset
          </div>
        </div>
        """

    p1.markdown(_proj_card("Daily Projection",   proj["daily_co2"],   proj["daily_cost"],   proj["trees_daily"],  THEME["green"]),  unsafe_allow_html=True)
    p2.markdown(_proj_card("Weekly Projection",  proj["weekly_co2"],  proj["weekly_cost"],  proj["trees_daily"]*7, THEME["accent"]), unsafe_allow_html=True)
    p3.markdown(_proj_card("Monthly Projection", proj["monthly_co2"], proj["monthly_cost"], trees_needed(proj["monthly_co2"]), THEME["yellow"]), unsafe_allow_html=True)
    p4.markdown(_proj_card("Yearly Projection",  proj["yearly_co2"],  proj["yearly_cost"],  proj["trees_yearly"], THEME["red"]),    unsafe_allow_html=True)

    # Projection bar chart
    st.markdown("### 📊 Projected CO₂ Accumulation")
    proj_periods = ["Session\n(now)", "Daily", "Weekly", "Monthly", "Yearly"]
    proj_vals    = [
        round(st.session_state.cumulative_co2, 1),
        proj["daily_co2"],
        proj["weekly_co2"],
        proj["monthly_co2"],
        proj["yearly_co2"],
    ]
    fig_proj = go.Figure(go.Bar(
        x=proj_periods, y=proj_vals,
        marker_color=[THEME["green"], THEME["accent"], THEME["yellow"], THEME["orange"], THEME["red"]],
        text=[f"{v} kg" for v in proj_vals],
        textposition="outside",
        textfont=dict(family="IBM Plex Mono", size=11),
    ))
    fig_proj.update_layout(
        template=THEME["plotly"], height=320,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis_title="CO₂ (kg)",
        showlegend=False,
    )
    st.plotly_chart(fig_proj, use_container_width=True)

    # Comparison: current model vs best model projections
    st.markdown("### 🆚 Model Switch Savings")
    best_model = min(MODEL_SPECS.items(), key=lambda x: x[1]["base_co2"])[0]
    if model != best_model:
        ratio = MODEL_SPECS[best_model]["base_co2"] / MODEL_SPECS[model]["base_co2"]
        savings_yearly_co2  = round(proj["yearly_co2"]  * (1 - ratio), 1)
        savings_yearly_cost = round(proj["yearly_cost"] * (1 - ratio), 2)
        savings_trees       = trees_needed(savings_yearly_co2)
        col_s1, col_s2 = st.columns(2)
        col_s1.success(
            f"💡 Switching from **{model}** to **{best_model}** could save approx. "
            f"**{savings_yearly_co2} kg CO₂/year** ({round((1-ratio)*100)}% reduction)"
        )
        col_s2.info(
            f"💰 Estimated annual carbon cost saving: **${savings_yearly_cost}**  \n"
            f"🌳 Offset trees freed per year: **{savings_trees}**"
        )
    else:
        st.success(f"✅ You're already on the most efficient model: **{model}**")

# ================================================================
# EXPORT
# ================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-pill">Export</div>', unsafe_allow_html=True)

ex1, ex2, ex3 = st.columns(3)
with ex1:
    csv = st.session_state.data.to_csv(index=False).encode()
    st.download_button(
        "📁 Download CSV",
        csv, "sustainability_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
with ex2:
    pdf_data = export_pdf(st.session_state.data)
    if pdf_data:
        st.download_button(
            "📄 Download PDF Report",
            pdf_data, "sustainability_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.info("Install `reportlab` for PDF export: `pip install reportlab`")
with ex3:
    # NEW: Export alert log
    if st.session_state.alert_log:
        al_csv = pd.DataFrame(st.session_state.alert_log).to_csv(index=False).encode()
        st.download_button(
            "🔔 Export Alert Log",
            al_csv, "alert_log.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.button("🔔 Export Alert Log", disabled=True, use_container_width=True)

# ---- NEW: Session summary footer ----
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
sc_summary = compute_scorecard(st.session_state.data, model)
st.markdown(f"""
<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;
            padding:14px 20px;display:flex;justify-content:space-between;align-items:center;
            font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--muted);">
  <span>v4 · AI Sustainability Dashboard</span>
  <span>Session Score: <strong style="color:{score_color(sc_summary['overall'])};">{sc_summary['overall']}/100</strong></span>
  <span>Uptime: {elapsed}</span>
  <span>Model: <strong style="color:var(--accent);">{model}</strong></span>
  <span>Total Queries: {st.session_state.total_queries:,}</span>
</div>
""", unsafe_allow_html=True)
