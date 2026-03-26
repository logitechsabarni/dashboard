# ================= AI SUSTAINABILITY DASHBOARD v3 =================
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
# Model specs are technical constants derived from published
# estimates.  Change them here (or move to models.json) rather
# than exposing them as sidebar widgets.
MODEL_SPECS = {
    "Claude Sonnet 4.6":  {"base_co2": 0.30, "base_power": 1.5, "efficiency": 0.88},
    "Claude Opus 4.6":    {"base_co2": 0.55, "base_power": 2.8, "efficiency": 0.75},
    "GPT-5.4":            {"base_co2": 0.50, "base_power": 2.5, "efficiency": 0.78},
    "Gemini 3.1 Pro":     {"base_co2": 0.42, "base_power": 2.1, "efficiency": 0.82},
    "Sonar":              {"base_co2": 0.22, "base_power": 1.1, "efficiency": 0.92},
    "Nemotron 3 Super":   {"base_co2": 0.60, "base_power": 3.0, "efficiency": 0.70},
}

CARBON_PRICE_PER_KG   = 0.02   # $/kg CO2
TREE_ABSORPTION_KG_YR = 21.77  # avg kg CO2 absorbed per tree per year
MAX_SIM_ITERATIONS    = 500
SLEEP_INTERVAL        = 0.7    # seconds between sim ticks
AI_SUMMARY_INTERVAL   = 30     # seconds between auto AI summaries

# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(
    page_title="AI Sustainability Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# THEME  — uses Streamlit-native token names where possible;
# CSS overrides only for things Streamlit can't do natively.
# ================================================================
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=True)

THEME = {
    "bg":       "#0a0d14" if dark_mode else "#f0f2f8",
    "card":     "#131720" if dark_mode else "#ffffff",
    "surface":  "#1c2130" if dark_mode else "#eef0f7",
    "border":   "#2a3045" if dark_mode else "#d8dce8",
    "text":     "#e2e8f0" if dark_mode else "#1a2035",
    "muted":    "#64748b" if dark_mode else "#94a3b8",
    "accent":   "#38bdf8",   # sky-400  — same in both modes for brand consistency
    "green":    "#34d399",
    "yellow":   "#fbbf24",
    "orange":   "#fb923c",
    "red":      "#f87171",
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
  }}

  html, body, [class*="css"] {{
    font-family: 'Sora', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text);
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
    transition: border-color 0.2s;
  }}
  [data-testid="stMetric"]:hover {{ border-top-color: var(--green); }}
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
</style>
""", unsafe_allow_html=True)

# ================================================================
# SIDEBAR  — only truly runtime-user-configurable params here
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

# Validate threshold ordering — logical guard
if not (co2_medium < co2_high < co2_critical):
    st.sidebar.error("Thresholds must satisfy: Medium < High < Critical")

st.sidebar.markdown("---")
st.sidebar.markdown('<p style="font-family:IBM Plex Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);">AI Engine</p>', unsafe_allow_html=True)
ANTHROPIC_API_KEY = st.sidebar.text_input(
    "Anthropic API Key", type="password", placeholder="sk-ant-...",
    help="Used only for AI Insights tab and auto-summaries. Never stored.",
    label_visibility="collapsed"
)

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
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
    """Holt's linear (double exponential) smoothing — better than polyfit for noisy series."""
    y = series.values.astype(float)
    if len(y) < 3:
        return np.full(steps, y[-1])
    # Holt's method
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
        doc.build(story)
        buf.seek(0)
        return buf.read()
    except ImportError:
        return None


# ================================================================
# HEADER
# ================================================================
elapsed = str(datetime.now() - st.session_state.session_start).split(".")[0]
mode_colors = {
    "normal": THEME["green"], "spike": THEME["red"],
    "low":    THEME["accent"], "high": THEME["orange"],
}
mode_color = mode_colors.get(st.session_state.mode, THEME["accent"])

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;
            padding-bottom:12px;border-bottom:1px solid {THEME['border']};margin-bottom:16px;">
  <div>
    <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;
                letter-spacing:.12em;text-transform:uppercase;color:{THEME['muted']};
                margin-bottom:4px;">AI Sustainability Monitor · v3</div>
    <h1 style="margin:0;font-size:1.7rem;">⚡ Emissions Dashboard</h1>
  </div>
  <div style="text-align:right;font-family:'IBM Plex Mono',monospace;font-size:12px;
              color:{THEME['muted']};">
    <div>Model: <span style="color:{THEME['accent']}">{model}</span></div>
    <div>Session: <span style="color:{THEME['text']}">{elapsed}</span></div>
    <div>Mode:
      <span style="color:{mode_color};font-weight:600;
                   text-transform:uppercase;">{st.session_state.mode}</span>
    </div>
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

row2 = st.columns(3)
row2[0].metric("🌳 Trees Needed / yr",  str(trees))
row2[1].metric("📦 Cumul. CO₂ (kg)",    round(st.session_state.cumulative_co2, 2))
row2[2].metric("⚡ Cumul. Power (kWh)", round(st.session_state.cumulative_power, 2))

# ================================================================
# CONTROLS — two logical groups, clearly separated
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
        if st.button("⚠️ Spike",  use_container_width=True): st.session_state.mode = "spike"
    with b2:
        if st.button("📉 Reduce", use_container_width=True): st.session_state.mode = "low"
    with b3:
        if st.button("🚀 Boost",  use_container_width=True): st.session_state.mode = "high"
    with b4:
        if st.button("✅ Normal", use_container_width=True): st.session_state.mode = "normal"

st.markdown("<hr>", unsafe_allow_html=True)

# ================================================================
# TABS
# ================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Real-Time",
    "📊 Analytics",
    "📈 Advanced",
    "🧠 AI Insights",
    "🤖 Model Compare",
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
        fig.add_trace(go.Scatter(
            x=forecast_times, y=forecast_vals,
            name="CO₂ Forecast", mode="lines",
            line=dict(color=THEME["orange"], dash="dot", width=2)
        ))
        if not anomalies_.empty:
            fig.add_trace(go.Scatter(
                x=anomalies_["time"], y=anomalies_["co2"],
                mode="markers", name="Anomaly",
                marker=dict(size=10, color=THEME["red"], symbol="x",
                            line=dict(width=2, color="#fff"))
            ))
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

            new_row = {"time": now, "queries": queries, "co2": co2, "power": power}
            st.session_state.data = pd.concat(
                [st.session_state.data, pd.DataFrame([new_row])], ignore_index=True
            ).tail(window)

            df_ = st.session_state.data.copy()
            avg_co2_ = df_["co2"].tail(5).mean()
            sl, sc = get_status(avg_co2_)

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

            # Auto AI summary — only if metrics changed meaningfully
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

    # Smoothed trends
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

    # Forecast
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

    # Correlation heatmap
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

    # Carbon offset
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
        df_sample = df.iloc[::max(1, len(df)//60)]   # cap to ~60 points for 3D perf

        # 3D scatter
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

        # Load vs Emissions
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

        # Anomaly detection
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

    # Health assessment
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

    # Recommendations
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

    # Scenario simulation
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

    # Chat
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

    # Highlight current model
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

    best  = compare_df.iloc[0]["Model"]
    worst = compare_df.iloc[-1]["Model"]
    st.success(f"✅ Most efficient at current load: **{best}**")
    if model == worst:
        st.warning(f"⚠️ You are using **{model}**, which has the highest estimated CO₂. "
                   f"Consider switching to **{best}** for a "
                   f"{round((1 - MODEL_SPECS[best]['base_co2']/MODEL_SPECS[model]['base_co2'])*100)}% reduction.")

# ================================================================
# EXPORT
# ================================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<div class="section-pill">Export</div>', unsafe_allow_html=True)

ex1, ex2 = st.columns(2)
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
