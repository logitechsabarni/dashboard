import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import requests
import datetime
from streamlit_autorefresh import st_autorefresh

# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------
st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ----------------------------------------------------
# AUTO REFRESH (REAL TIME)
# ----------------------------------------------------
st_autorefresh(interval=5000, key="refresh")

# ----------------------------------------------------
# LIVE CARBON INTENSITY API
# ----------------------------------------------------
def get_live_carbon():
    try:
        url = "https://api.carbonintensity.org.uk/intensity"
        res = requests.get(url).json()
        return res["data"][0]["intensity"]["actual"]
    except:
        return 300

live_carbon = get_live_carbon()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("🟢 Executive AI Sustainability Dashboard")
st.markdown("Monitor, analyze, and optimize corporate AI usage to reduce environmental impact.")
st.markdown("🔴 **LIVE AI Monitoring Enabled**")
st.markdown("---")

# ----------------------------------------------------
# REAL TIME QUERY LOGGER
# ----------------------------------------------------
models = ["GPT-4","GPT-4o","GPT-3.5","Gemini-Pro","Gemini-Flash","Claude-Haiku"]

if "query_logs" not in st.session_state:
    st.session_state.query_logs = []

# ----------------------------------------------------
# HERO METRICS
# ----------------------------------------------------
hero_metrics = {
    "Score": 85.8,
    "MSE": 93.3,
    "CFD": 0.85,
    "TUA": 80.0
}

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Corporate Sustainability Score", f"{hero_metrics['Score']} / 100")

with col2:
    st.metric("Model Selection Efficiency", f"{hero_metrics['MSE']}%")

with col3:
    st.metric("Daily Carbon Footprint", f"{hero_metrics['CFD']} g CO2")

with col4:
    st.metric("Live Grid Carbon", f"{live_carbon} gCO2/kWh")

st.markdown("---")

# ----------------------------------------------------
# SIDEBAR CONTROLS
# ----------------------------------------------------
st.sidebar.header("⚙ AI Emission Controls")

deepseek = st.sidebar.slider("DeepSeek CO2 per Query (g)",0.01,10.0,5.0)
gpt4 = st.sidebar.slider("GPT-4 CO2 per Query (g)",0.01,5.0,0.5)
claude_opus = st.sidebar.slider("Claude 3 Opus CO2 per Query (g)",0.01,5.0,0.5)
gemini_ultra = st.sidebar.slider("Gemini Ultra CO2 per Query (g)",0.01,5.0,0.5)
gpt4o = st.sidebar.slider("GPT-4o CO2 per Query (g)",0.01,2.0,0.15)
gpt35 = st.sidebar.slider("GPT-3.5 CO2 per Query (g)",0.01,1.0,0.05)
gemini_pro = st.sidebar.slider("Gemini Pro CO2 per Query (g)",0.01,1.0,0.05)
claude_haiku = st.sidebar.slider("Claude Haiku CO2 per Query (g)",0.01,1.0,0.05)
gemini_flash = st.sidebar.slider("Gemini Flash CO2 per Query (g)",0.01,1.0,0.03)

queries = st.sidebar.slider("Total Daily AI Queries",100,10000,1000,step=100)

migration_pct = st.sidebar.slider(
"GPT-4 Queries Migrated → Gemini Flash (%)",
0,100,30,step=5
)

# ----------------------------------------------------
# REAL TIME LOGGING
# ----------------------------------------------------
model_used = np.random.choice(models)

timestamp = datetime.datetime.now()

co2_lookup = {
"GPT-4":gpt4,
"GPT-4o":gpt4o,
"GPT-3.5":gpt35,
"Gemini-Pro":gemini_pro,
"Gemini-Flash":gemini_flash,
"Claude-Haiku":claude_haiku
}

co2 = co2_lookup[model_used]

log = {
"Time":timestamp.strftime("%H:%M:%S"),
"Model":model_used,
"CO2":co2
}

st.session_state.query_logs.append(log)

if len(st.session_state.query_logs) > 100:
    st.session_state.query_logs.pop(0)

query_df = pd.DataFrame(st.session_state.query_logs)

# ----------------------------------------------------
# QUERY DISTRIBUTION
# ----------------------------------------------------
gpt4_queries = queries*(1-migration_pct/100)
gemini_flash_queries = queries*(migration_pct/100)

# ----------------------------------------------------
# TOTAL EMISSIONS
# ----------------------------------------------------
total_emissions = {
"DeepSeek":deepseek*queries*0.02,
"GPT-4":gpt4*gpt4_queries,
"Claude-3-Opus":claude_opus*queries*0.05,
"Gemini-Ultra":gemini_ultra*queries*0.05,
"GPT-4o":gpt4o*queries*0.08,
"GPT-3.5":gpt35*queries*0.2,
"Gemini-Pro":gemini_pro*queries*0.15,
"Claude-Haiku":claude_haiku*queries*0.1,
"Gemini-Flash":gemini_flash*gemini_flash_queries
}

model_emissions=pd.DataFrame({
"Model":list(total_emissions.keys()),
"Total CO2 (g)":list(total_emissions.values())
}).sort_values(by="Total CO2 (g)",ascending=True)

# ----------------------------------------------------
# MAIN VISUALIZATION
# ----------------------------------------------------
col_left,col_right=st.columns(2)

with col_left:

    st.subheader("Algorithm Parameter Breakdown")

    parameters=['Query Frequency','Model Selection','Query Complexity','Time-of-Use','Daily Carbon','Session Efficiency']
    weights=[20,25,15,10,20,10]
    user_performance=[18,23,14,8,17,8]

    fig_radar=go.Figure()

    fig_radar.add_trace(go.Scatterpolar(r=weights,theta=parameters,fill='toself',name='Max Allocation'))
    fig_radar.add_trace(go.Scatterpolar(r=user_performance,theta=parameters,fill='toself',name='Current Performance'))

    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,30])))

    st.plotly_chart(fig_radar,use_container_width=True)

with col_right:

    st.subheader("Total CO2 Emissions by AI Model")

    fig_bar=px.bar(
    model_emissions,
    x="Total CO2 (g)",
    y="Model",
    orientation='h',
    color="Total CO2 (g)",
    color_continuous_scale="RdYlGn_r",
    text="Total CO2 (g)"
    )

    st.plotly_chart(fig_bar,use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# LIVE ACTIVITY FEED
# ----------------------------------------------------
st.subheader("🔴 Live AI Activity Feed")

st.dataframe(query_df,use_container_width=True)

# ----------------------------------------------------
# MODEL USAGE CHART
# ----------------------------------------------------
st.subheader("Live Model Usage")

usage=query_df["Model"].value_counts().reset_index()
usage.columns=["Model","Queries"]

fig_usage=px.bar(usage,x="Model",y="Queries",color="Queries")

st.plotly_chart(fig_usage,use_container_width=True)

# ----------------------------------------------------
# SUSTAINABILITY GAUGE
# ----------------------------------------------------
total_live_co2=query_df["CO2"].sum()
sustainability_score=max(0,100-total_live_co2*0.5)

st.subheader("AI Sustainability Risk Indicator")

fig=go.Figure(go.Indicator(
mode="gauge+number",
value=sustainability_score,
title={'text':"Sustainability Score"},
gauge={'axis':{'range':[0,100]},
'steps':[
{'range':[0,60],'color':"red"},
{'range':[60,80],'color':"yellow"},
{'range':[80,100],'color':"lightgreen"}
]}
))

st.plotly_chart(fig,use_container_width=True)

# ----------------------------------------------------
# PEAK LOAD ALERT
# ----------------------------------------------------
st.subheader("AI Load Monitoring")

if len(query_df)>80:
    st.error("⚠ High AI traffic detected")

elif len(query_df)>40:
    st.warning("⚡ Moderate AI usage")

else:
    st.success("🌱 AI usage within sustainable limits")

st.markdown("---")

# ----------------------------------------------------
# STRATEGY SIMULATOR
# ----------------------------------------------------
st.subheader("Strategy Simulator")

original_emissions=queries*gpt4

new_emissions=(gpt4_queries*gpt4+gemini_flash_queries*gemini_flash)

savings=original_emissions-new_emissions

st.info(f"Predicted Daily Carbon Savings: **{savings:.2f} g CO2**")

efficiency_gain=migration_pct*0.15

st.success(f"Projected Model Efficiency Increase: **+{efficiency_gain:.2f}%**")

st.metric("Total Queries Analysed",queries)

# ----------------------------------------------------
# RECOMMENDATION ENGINE
# ----------------------------------------------------
st.subheader("AI Sustainability Recommendations")

if migration_pct<40:
    st.warning("⚠ Increase lightweight model migration to reduce emissions.")

if queries>5000:
    st.info("💡 High AI usage detected. Consider batching requests or lighter models.")

if savings>200:
    st.success("✅ Current strategy significantly reduces carbon emissions.")

if sustainability_score>80:
    st.success("🌱 Your AI infrastructure is operating sustainably.")
