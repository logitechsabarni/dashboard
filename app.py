import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ---------------- DARK MODE ----------------
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)
bg = "#0f172a" if dark_mode else "#f5f7fa"
card_bg = "#111827" if dark_mode else "white"
text_color = "white" if dark_mode else "black"

# ---------------- CSS ----------------
st.markdown(f"""
<style>
.main {{background-color: {bg}; color: {text_color};}}
.card {{
    background: {card_bg};
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}}
.section-title {{font-size: 18px; font-weight: 600; margin-bottom: 10px;}}
.metric {{font-size: 24px; font-weight: bold;}}
.sub {{color: gray; font-size: 13px;}}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")
model = st.sidebar.selectbox(
    "Select Model",
    ["Sonar", "GPT-5.4", "Gemini 3.1 Pro", "Claude Sonnet 4.6", "Claude Opus 4.6", "Nemotron 3 Super"]
)

# ---------------- DATA ----------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(10)),
        "queries": np.random.randint(20, 120, 10),
        "co2": np.random.randint(10, 60, 10),
        "power": np.random.randint(200, 400, 10)
    })

# simulate live update
new_point = {
    "time": st.session_state.data["time"].iloc[-1] + 1,
    "queries": np.random.randint(20, 120),
    "co2": np.random.randint(10, 60),
    "power": np.random.randint(200, 400)
}
st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_point])], ignore_index=True)
st.session_state.data = st.session_state.data.tail(30)

# ---------------- HEADER ----------------
col1, col2, col3, col4 = st.columns([1,2,2,2])
with col1:
    st.markdown("### SS")
with col2:
    st.metric("Queries", int(st.session_state.data["queries"].iloc[-1]))
with col3:
    st.metric("CO2", f"{int(st.session_state.data['co2'].iloc[-1])} kg")
with col4:
    st.metric("Power", f"{int(st.session_state.data['power'].iloc[-1])} kWh")

# ---------------- LAYOUT ----------------
left, right = st.columns([2,1])

# -------- LEFT --------
with left:
    st.markdown("<div class='section-title'>Usage Timeline</div>", unsafe_allow_html=True)
    st.line_chart(st.session_state.data.set_index("time")["queries"])

    st.markdown("<div class='section-title'>Trend Comparison</div>", unsafe_allow_html=True)
    st.line_chart(st.session_state.data.set_index("time")[["queries","co2"]])

    st.markdown("<div class='section-title'>Power Consumption Trend</div>", unsafe_allow_html=True)
    st.area_chart(st.session_state.data.set_index("time")["power"])

    st.markdown("<div class='section-title'>CO2 Prediction (Next Steps)</div>", unsafe_allow_html=True)
    future = np.arange(30, 40)
    predicted = np.linspace(st.session_state.data['co2'].iloc[-1], st.session_state.data['co2'].iloc[-1] - 10, 10)
    pred_df = pd.DataFrame({"time": future, "predicted_co2": predicted})
    st.line_chart(pred_df.set_index("time"))

    st.markdown("<div class='section-title'>Model Distribution</div>", unsafe_allow_html=True)
    model_data = pd.DataFrame({
        "model": ["Sonar", "GPT", "Gemini", "Claude"],
        "usage": np.random.randint(10,60,4)
    })
    st.bar_chart(model_data.set_index("model"))

    st.markdown("<div class='section-title'>System Visualization</div>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71", use_container_width=True)

# -------- RIGHT --------
with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Session Stats</div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='metric'>{len(st.session_state.data)} Sessions</div>
        <div class='sub'>Avg Duration: 5 mins</div>
    """, unsafe_allow_html=True)

    st.write("---")

    st.markdown("<div class='section-title'>AI Insights</div>", unsafe_allow_html=True)
    st.info(f"Using {model}: Shift workloads to off-peak hours to reduce emissions.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- MODEL INFERENCE ----------------
st.markdown("### 🧠 Model Inference")
input_text = st.text_area("Enter query for analysis")

if st.button("Analyze"):
    st.success(f"Model {model} suggests optimizing compute scheduling and batching.")

# ---------------- REPORT DOWNLOAD ----------------
st.markdown("### 📄 Download Report")
report_text = f"""
AI Sustainability Report

Model Used: {model}
Latest Queries: {int(st.session_state.data['queries'].iloc[-1])}
Latest CO2: {int(st.session_state.data['co2'].iloc[-1])} kg
Latest Power: {int(st.session_state.data['power'].iloc[-1])} kWh

Insight: Optimize workloads to reduce emissions.
"""

st.download_button("Download Report", report_text, file_name="report.txt")

# ---------------- FOOTER ----------------
st.write("\n\n")

# Run:
# streamlit run filename.py
