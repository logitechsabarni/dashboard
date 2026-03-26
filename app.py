import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ---------------- THEME ----------------
dark_mode = st.sidebar.toggle("🌙 Dark Mode", value=False)
bg = "#0f172a" if dark_mode else "#f5f7fa"
card_bg = "#111827" if dark_mode else "white"
text_color = "white" if dark_mode else "black"
accent = "#22c55e"

st.markdown(f"""
<style>
.main {{background-color: {bg}; color: {text_color};}}
.card {{background: {card_bg}; padding:18px; border-radius:18px; box-shadow:0 8px 24px rgba(0,0,0,0.12);}}
.section-title {{font-size:18px; font-weight:600; margin-bottom:10px;}}
.metric {{font-size:26px; font-weight:700;}}
.sub {{color:gray; font-size:13px;}}
.badge {{background:{accent}; color:white; padding:4px 10px; border-radius:999px; font-size:12px;}}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")
model = st.sidebar.selectbox("Select Model", ["Sonar","GPT-5.4","Gemini 3.1 Pro","Claude Sonnet 4.6","Claude Opus 4.6","Nemotron 3 Super"])
range_filter = st.sidebar.slider("Time Window", 10, 60, 30)
notif = st.sidebar.checkbox("🔔 Enable Alerts", value=True)

# ---------------- DATA ----------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(10)),
        "queries": np.random.randint(20,120,10),
        "co2": np.random.randint(10,60,10),
        "power": np.random.randint(200,400,10)
    })

new = {
    "time": st.session_state.data["time"].iloc[-1] + 1,
    "queries": np.random.randint(20,120),
    "co2": np.random.randint(10,60),
    "power": np.random.randint(200,400)
}
st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new])], ignore_index=True)
st.session_state.data = st.session_state.data.tail(range_filter)

latest = st.session_state.data.iloc[-1]

# ---------------- HEADER ----------------
col1,col2,col3,col4,col5 = st.columns([1.2,2,2,2,1.5])
with col1: st.markdown("### SS")
with col2: st.metric("Queries", int(latest["queries"]))
with col3: st.metric("CO2", f"{int(latest['co2'])} kg")
with col4: st.metric("Power", f"{int(latest['power'])} kWh")
with col5: st.markdown(f"<div class='badge'>{model}</div>", unsafe_allow_html=True)

# ---------------- ALERTS ----------------
if notif and latest["co2"] > 50:
    st.warning("⚠️ High CO2 detected! Consider reducing load.")

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📊 Analytics","🧠 AI Insights","📁 Data"])

# -------- TAB 1: ANALYTICS --------
with tab1:
    left,right = st.columns([2,1])

    with left:
        st.markdown("<div class='section-title'>Usage Timeline</div>", unsafe_allow_html=True)
        st.line_chart(st.session_state.data.set_index("time")["queries"])

        st.markdown("<div class='section-title'>Trend Comparison</div>", unsafe_allow_html=True)
        st.line_chart(st.session_state.data.set_index("time")[["queries","co2"]])

        st.markdown("<div class='section-title'>Power Consumption</div>", unsafe_allow_html=True)
        st.area_chart(st.session_state.data.set_index("time")["power"])

        st.markdown("<div class='section-title'>CO2 Prediction</div>", unsafe_allow_html=True)
        future = np.arange(range_filter, range_filter+10)
        pred = np.linspace(latest['co2'], latest['co2']-10, 10)
        st.line_chart(pd.DataFrame({"time":future,"pred":pred}).set_index("time"))

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Session Stats</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='metric'>{len(st.session_state.data)}</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub'>Active Sessions</div>", unsafe_allow_html=True)
        st.write("---")
        st.markdown("<div class='section-title'>Model Usage</div>", unsafe_allow_html=True)
        m = pd.DataFrame({"model":["Sonar","GPT","Gemini","Claude"],"usage":np.random.randint(10,60,4)})
        st.bar_chart(m.set_index("model"))
        st.markdown("</div>", unsafe_allow_html=True)

# -------- TAB 2: AI INSIGHTS --------
with tab2:
    st.markdown("### 🤖 Smart Insights")
    st.success(f"{model}: Optimize batching + shift workloads to off-peak.")

    st.markdown("### 🧠 Inference")
    txt = st.text_area("Enter query")
    if st.button("Run Model"):
        st.info(f"{model} → Reduce redundant calls & compress workloads.")

# -------- TAB 3: DATA --------
with tab3:
    st.markdown("### 📁 Raw Data")
    st.dataframe(st.session_state.data)

    csv = st.session_state.data.to_csv(index=False).encode()
    st.download_button("⬇️ Export CSV", csv, "data.csv")

    st.markdown("### 📄 Generate Report")
    report = f"Model: {model}\nQueries: {int(latest['queries'])}\nCO2: {int(latest['co2'])}\nPower: {int(latest['power'])}"
    st.download_button("Download Report", report, "report.txt")

# ---------------- FOOTER ----------------
st.write("\n\n")

# Run:
# streamlit run filename.py
