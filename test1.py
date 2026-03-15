import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime
from streamlit_autorefresh import st_autorefresh

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ----------------------------------------------------
# AUTO REFRESH
# ----------------------------------------------------
st_autorefresh(interval=5000, key="dashboardrefresh")

st.title("🟢 Executive AI Sustainability Dashboard")
st.markdown("Monitor, analyze, and optimize corporate AI usage to reduce environmental impact.")
st.markdown("---")

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
st.sidebar.header("⚙ AI Emission Controls")

deepseek = st.sidebar.slider("DeepSeek CO2 per Query (g)", 0.01, 10.0, 5.0)
gpt4 = st.sidebar.slider("GPT-4 CO2 per Query (g)", 0.01, 5.0, 0.5)
claude_opus = st.sidebar.slider("Claude 3 Opus CO2 per Query (g)", 0.01, 5.0, 0.5)
gemini_ultra = st.sidebar.slider("Gemini Ultra CO2 per Query (g)", 0.01, 5.0, 0.5)
gpt4o = st.sidebar.slider("GPT-4o CO2 per Query (g)", 0.01, 2.0, 0.15)
gpt35 = st.sidebar.slider("GPT-3.5 CO2 per Query (g)", 0.01, 1.0, 0.05)
gemini_pro = st.sidebar.slider("Gemini Pro CO2 per Query (g)", 0.01, 1.0, 0.05)
claude_haiku = st.sidebar.slider("Claude Haiku CO2 per Query (g)", 0.01, 1.0, 0.05)
gemini_flash = st.sidebar.slider("Gemini Flash CO2 per Query (g)", 0.01, 1.0, 0.03)

st.sidebar.markdown("---")

queries = st.sidebar.slider("Total Daily AI Queries", 100, 10000, 1000, step=100)

migration_pct = st.sidebar.slider(
    "GPT-4 Queries Migrated → Gemini Flash (%)",
    0, 100, 30, step=5
)

# ----------------------------------------------------
# QUERY DISTRIBUTION
# ----------------------------------------------------
gpt4_queries = queries * (1 - migration_pct / 100)
gemini_flash_queries = queries * (migration_pct / 100)

# ----------------------------------------------------
# TOTAL EMISSIONS
# ----------------------------------------------------
total_emissions = {
    "DeepSeek": deepseek * queries * 0.02,
    "GPT-4": gpt4 * gpt4_queries,
    "Claude-3-Opus": claude_opus * queries * 0.05,
    "Gemini-Ultra": gemini_ultra * queries * 0.05,
    "GPT-4o": gpt4o * queries * 0.08,
    "GPT-3.5": gpt35 * queries * 0.2,
    "Gemini-Pro": gemini_pro * queries * 0.15,
    "Claude-Haiku": claude_haiku * queries * 0.1,
    "Gemini-Flash": gemini_flash * gemini_flash_queries
}

total_daily_emissions = sum(total_emissions.values())

model_emissions = pd.DataFrame({
    "Model": list(total_emissions.keys()),
    "Total CO2 (g)": list(total_emissions.values())
}).sort_values(by="Total CO2 (g)", ascending=True)

# ----------------------------------------------------
# HERO METRICS (DYNAMIC)
# ----------------------------------------------------
sustainability_score = max(0, 100 - (total_daily_emissions / 50))
model_efficiency = 70 + (migration_pct * 0.3)
daily_carbon = total_daily_emissions / queries
time_use = min(100, 50 + (migration_pct * 0.5))
hero_metrics = {
    "Score": sustainability_score,
    "MSE": model_efficiency,
    "CFD": daily_carbon,
    "TUA": time_use
}

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Corporate Sustainability Score",
        value=f"{hero_metrics['Score']:.2f} / 100",
        delta=f"+{score_delta:.2f} vs Last Month"
        delta_color="normal"
    )

with col2:
    st.metric(
        label="Model Selection Efficiency (MSE)",
        value=f"{hero_metrics['MSE']:.2f}%",
        delta=f"+{migration_pct*0.15:.1f}% vs Last Month"
    )

with col3:
    st.metric(
        label="Daily Carbon Footprint (CFD)",
        value=f"{hero_metrics['CFD']:.3f} g CO2",
        delta=f"-{migration_pct*0.05:.2f}g vs Last Month",
        delta_color="inverse"
    )

with col4:
    st.metric(
        label="Time-of-Use Awareness (TUA)",
        value=f"{hero_metrics['TUA']:.2f}%",
        delta="Peak Green Hours"
    )


st.markdown("---")

# ----------------------------------------------------
# RADAR PARAMETERS
# ----------------------------------------------------
query_score = min(20, (queries / 5000) * 20)
model_score = min(25, (migration_pct / 100) * 25)
complexity_score = min(15, (gpt4 + claude_opus + gemini_ultra) * 2)
time_score = min(10, (time_use / 100) * 10)
carbon_score = min(20, (daily_carbon / 2) * 20)
session_score = min(10, (migration_pct / 100) * 10)

user_performance = [
    query_score,
    model_score,
    complexity_score,
    time_score,
    carbon_score,
    session_score
]

parameters = [
    "Query Frequency",
    "Model Selection",
    "Query Complexity",
    "Time-of-Use",
    "Daily Carbon",
    "Session Efficiency"
]

weights = [20, 25, 15, 10, 20, 10]

# ----------------------------------------------------
# MAIN VISUALIZATION
# ----------------------------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Algorithm Parameter Breakdown")

    fig_radar = go.Figure()

    fig_radar.add_trace(go.Scatterpolar(
        r=weights,
        theta=parameters,
        fill='toself',
        name='Max Allocation'
    ))

    fig_radar.add_trace(go.Scatterpolar(
        r=user_performance,
        theta=parameters,
        fill='toself',
        name='Current Performance'
    ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 30])),
        template="plotly_white"
    )

    st.plotly_chart(fig_radar, use_container_width=True)

with col_right:
    st.subheader("Total CO2 Emissions by AI Model")

    fig_bar = px.bar(
        model_emissions,
        x="Total CO2 (g)",
        y="Model",
        orientation='h',
        color="Total CO2 (g)",
        color_continuous_scale="RdYlGn_r",
        text="Total CO2 (g)"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# RISK GAUGE
# ----------------------------------------------------
st.subheader("AI Sustainability Risk Indicator")

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=sustainability_score,
    title={'text': "Sustainability Score"},
    gauge={
        'axis': {'range': [0, 100]},
        'steps': [
            {'range': [0, 60], 'color': "red"},
            {'range': [60, 80], 'color': "yellow"},
            {'range': [80, 100], 'color': "lightgreen"}
        ]
    }
))

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# TEMPORAL CARBON ANALYSIS (DYNAMIC)
# ----------------------------------------------------
col_bottom_left, col_bottom_right = st.columns(2)

with col_bottom_left:
    st.subheader("Temporal Carbon Intensity")

    hours = list(range(24))
    base_queries = queries / 24

    query_volume = [
        int(base_queries * (1 + 0.8 * np.sin((h - 6) / 3)))
        for h in hours
    ]

    carbon_intensity = [
        (total_daily_emissions / 10) * (1 + np.sin((h - 6) / 4))
        for h in hours
    ]

    df_temporal = pd.DataFrame({
        "Hour": hours,
        "Query Volume": query_volume,
        "Carbon Intensity": carbon_intensity
    })

    fig_area = go.Figure()

    fig_area.add_trace(go.Scatter(
        x=df_temporal["Hour"],
        y=df_temporal["Carbon Intensity"],
        fill='tozeroy',
        name="Carbon Intensity",
        line=dict(width=3)
    ))

    fig_area.add_trace(go.Scatter(
        x=df_temporal["Hour"],
        y=df_temporal["Query Volume"],
        mode='lines+markers',
        name="AI Queries",
        line=dict(width=3)
    ))

    st.plotly_chart(fig_area, use_container_width=True)

# ----------------------------------------------------
# STRATEGY SIMULATOR
# ----------------------------------------------------
with col_bottom_right:
    st.subheader("Strategy Simulator")

    original_emissions = queries * gpt4
    new_emissions = (gpt4_queries * gpt4 + gemini_flash_queries * gemini_flash)

    savings = original_emissions - new_emissions

    st.info(f"Predicted Daily Carbon Savings: **{savings:.2f} g CO2**")

    efficiency_gain = migration_pct * 0.15

    st.success(f"Projected Model Efficiency Increase: **+{efficiency_gain:.2f}%**")

    st.metric("Total Queries Analysed", queries)

st.markdown("---")

# ----------------------------------------------------
# REAL TIME MONITORING
# ----------------------------------------------------
st.header("🔴 Real-Time AI Monitoring System")

models = ["GPT-4", "GPT-4o", "GPT-3.5", "Gemini-Pro", "Gemini-Flash", "Claude-Haiku"]

if "logs" not in st.session_state:
    st.session_state.logs = []

model = np.random.choice(models)
timestamp = datetime.datetime.now().strftime("%H:%M:%S")
co2 = np.random.uniform(0.02, 0.5)

st.session_state.logs.append({
    "Time": timestamp,
    "Model": model,
    "CO2": co2
})

if len(st.session_state.logs) > 50:
    st.session_state.logs.pop(0)

log_df = pd.DataFrame(st.session_state.logs)

st.subheader("Live AI Query Feed")
st.dataframe(log_df, use_container_width=True)

st.subheader("Live Model Usage")

usage = log_df["Model"].value_counts().reset_index()
usage.columns = ["Model", "Queries"]

fig_usage = px.bar(usage, x="Model", y="Queries", color="Queries")
st.plotly_chart(fig_usage, use_container_width=True)

st.subheader("Live CO2 Emission Distribution")

emissions = log_df.groupby("Model")["CO2"].sum().reset_index()

fig_pie = px.pie(emissions, names="Model", values="CO2")
st.plotly_chart(fig_pie, use_container_width=True)

total_live_co2 = log_df["CO2"].sum()
live_score = max(0, 100 - total_live_co2 * 5)

st.metric("Dynamic Sustainability Score", round(live_score, 2))

if len(log_df) > 40:
    st.error("⚠ High AI traffic detected")
else:
    st.success("🌱 AI usage within sustainable limits")

# ----------------------------------------------------
# AI SUSTAINABILITY INSIGHTS
# ----------------------------------------------------
st.markdown("---")
st.header("🤖 AI Sustainability Insights")

dashboard_data = f"""
Total Queries: {queries}
Migration Percentage: {migration_pct}
Total Daily CO2 Emissions: {total_daily_emissions:.2f} grams
Average CO2 per Query: {daily_carbon:.4f} grams
Live CO2 Emissions: {total_live_co2:.3f}
Sustainability Score: {sustainability_score:.2f}
"""

st.markdown("**Try sample questions:**")
st.markdown("""
- How can we reduce emissions?
- What is the current carbon footprint?
- What is the sustainability score?
- Which model is most sustainable?
- How much carbon are we saving?
""")

question = st.text_input("Ask a question about AI sustainability")

if st.button("Generate Insight"):
    q = question.strip().lower()

    original_emissions = queries * gpt4
    new_emissions = (gpt4_queries * gpt4 + gemini_flash_queries * gemini_flash)
    savings = original_emissions - new_emissions

    if q == "":
        st.warning("Please enter a question.")

    elif "reduce" in q and "emission" in q:
        answer = f"""
To reduce AI emissions, the company should shift more low-complexity queries from high-carbon models to lightweight models like Gemini Flash or GPT-3.5.

At the current migration level of {migration_pct}%, your platform is already reducing emissions. Increasing this migration further can improve sustainability without affecting simple task performance.
"""

    elif "best model" in q or "which model" in q or "most sustainable" in q:
        answer = """
For sustainability-focused deployment, lightweight models such as Gemini Flash, GPT-3.5, and Claude Haiku are more efficient for routine queries.

Heavier models like GPT-4, Claude 3 Opus, and Gemini Ultra should be used only for complex reasoning or high-value tasks.
"""

    elif "carbon footprint" in q or "co2" in q:
        answer = f"""
The current estimated total daily carbon footprint is {total_daily_emissions:.2f} grams of CO2.

The average carbon emission per query is {daily_carbon:.4f} grams. This means your current AI workload has measurable environmental impact, but further model optimization can reduce it.
"""

    elif "sustainability score" in q:
        answer = f"""
The current sustainability score is {sustainability_score:.2f} out of 100.

This score reflects AI query volume, model routing efficiency, daily emissions, and sustainable workload distribution.
"""

    elif "save" in q or "saving" in q or "savings" in q:
        answer = f"""
By migrating {migration_pct}% of GPT-4 queries to Gemini Flash, the company can save approximately {savings:.2f} grams of CO2 per day.

This also improves system efficiency and supports greener AI operations.
"""

    elif "recommend" in q or "suggest" in q:
        answer = """
Recommended sustainability actions:

1. Route simple queries to low-emission models.
2. Reserve large models for difficult analytical tasks only.
3. Monitor peak-hour query volume to avoid unnecessary energy spikes.
4. Continuously track model-wise carbon output using dashboard analytics.
"""

    else:
        answer = f"""
Based on the current dashboard data, the company is handling {queries} AI queries per day and migrating {migration_pct}% of GPT-4 traffic to Gemini Flash.

This indicates positive movement toward sustainable AI adoption. Additional gains can come from better model routing, lower reliance on high-emission models, and improved time-of-use strategies.
"""

    st.success("AI Insight")
    st.write(answer)
