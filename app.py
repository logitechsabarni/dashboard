# ================= ELITE FINAL DASHBOARD =================
# streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Sustainability System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM DARK UI ----------------
st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.metric-card {
    background: #1c1f26;
    padding: 15px;
    border-radius: 12px;
}
.big-title {
    font-size: 30px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ System Controls")

model = st.sidebar.selectbox("AI Model", [
    "Sonar","GPT-5.4","Gemini 3.1 Pro",
    "Claude Sonnet 4.6","Claude Opus 4.6","Nemotron 3 Super"
])

window = st.sidebar.slider("Time Window", 20, 100, 50)
intensity = st.sidebar.slider("⚡ Intensity", 1, 5, 3)

# ---------------- STATE ----------------
if "running" not in st.session_state:
    st.session_state.running = False

if "mode" not in st.session_state:
    st.session_state.mode = "normal"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(20)),
        "queries": np.random.randint(40,100,20),
        "co2": np.random.randint(20,50,20),
        "power": np.random.randint(200,350,20)
    })

df = st.session_state.data
latest = df.iloc[-1]

# ---------------- HEADER ----------------
st.markdown('<div class="big-title">⚡ AI Sustainability Monitoring System</div>', unsafe_allow_html=True)

# ---------------- METRICS ----------------
c1,c2,c3,c4 = st.columns(4)

c1.metric("Queries", int(latest["queries"]))
c2.metric("CO2 (kg)", int(latest["co2"]))
c3.metric("Power (kWh)", int(latest["power"]))
c4.metric("Mode", st.session_state.mode.upper())

# ---------------- CARBON COST ----------------
carbon_cost = latest["co2"] * 0.02

st.markdown("### 💰 Carbon Impact")
st.metric("Estimated Cost ($)", f"{carbon_cost:.2f}")

# ---------------- CONTROLS ----------------
st.markdown("### 🎛️ Control Panel")

col1,col2,col3 = st.columns(3)

with col1:
    if st.button("▶️ Start"):
        st.session_state.running = True

with col2:
    if st.button("⏸ Stop"):
        st.session_state.running = False

with col3:
    if st.button("🔄 Reset"):
        st.session_state.data = st.session_state.data.iloc[:20]
        st.session_state.mode = "normal"

# ---------------- MODES ----------------
st.markdown("### ⚡ System Behavior")

b1,b2,b3,b4 = st.columns(4)

with b1:
    if st.button("⚠️ Spike Mode"):
        st.session_state.mode = "spike"

with b2:
    if st.button("📉 Reduce Load"):
        st.session_state.mode = "low"

with b3:
    if st.button("🚀 Boost Traffic"):
        st.session_state.mode = "high"

with b4:
    if st.button("✅ Normalize"):
        st.session_state.mode = "normal"

# ---------------- REAL-TIME ----------------
st.markdown("## ⚡ Real-Time Monitoring")

chart = st.empty()
insight_box = st.empty()

if st.session_state.running:

    for _ in range(500):

        mode = st.session_state.mode
        factor = intensity

        # -------- MODE LOGIC --------
        if mode == "spike":
            queries = np.random.randint(100,150) * factor
            co2 = np.random.randint(70,100)
            power = np.random.randint(350,450)

        elif mode == "low":
            queries = np.random.randint(10,40) // factor
            co2 = np.random.randint(10,30)
            power = np.random.randint(150,250)

        elif mode == "high":
            queries = np.random.randint(120,180)
            co2 = np.random.randint(60,90)
            power = np.random.randint(300,450)

        else:
            queries = np.random.randint(40,100)
            co2 = np.random.randint(20,60)
            power = np.random.randint(200,350)

        new_row = {
            "time": df["time"].iloc[-1] + 1,
            "queries": queries,
            "co2": co2,
            "power": power
        }

        st.session_state.data = pd.concat([
            df, pd.DataFrame([new_row])
        ], ignore_index=True).tail(window)

        df = st.session_state.data
        latest = df.iloc[-1]

        # -------- ML ANOMALY --------
        mean = df["co2"].rolling(5).mean()
        std = df["co2"].rolling(5).std()

        anomalies = df[df["co2"] > (mean + 2*std)]

        # -------- AI INSIGHTS --------
        if latest["co2"] > 70:
            insight_box.error("🚨 AI: Critical emissions. Shift workload now.")
        elif latest["co2"] > 40:
            insight_box.warning("⚠️ AI: Optimize scheduling.")
        else:
            insight_box.success("✅ AI: Efficient system.")

        # -------- PREDICTION --------
        future_x = np.arange(df["time"].iloc[-1], df["time"].iloc[-1]+10)
        future_y = np.linspace(latest["co2"], latest["co2"]-10, 10)

        # -------- GRAPH --------
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df["time"], y=df["co2"],
                                 name="CO2", line=dict(color="red", width=3)))

        fig.add_trace(go.Scatter(x=df["time"], y=df["queries"], name="Queries"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["power"], name="Power"))

        # anomalies
        fig.add_trace(go.Scatter(
            x=anomalies["time"],
            y=anomalies["co2"],
            mode="markers",
            marker=dict(color="red", size=10),
            name="Anomaly"
        ))

        # prediction
        fig.add_trace(go.Scatter(
            x=future_x,
            y=future_y,
            mode="lines",
            line=dict(dash="dash"),
            name="Prediction"
        ))

        fig.update_layout(
            template="plotly_dark",
            height=450,
            title=f"Mode: {mode.upper()}"
        )

        chart.plotly_chart(fig, use_container_width=True)

        time.sleep(1)

        if not st.session_state.running:
            break

# ---------------- LEADERBOARD ----------------
st.markdown("## 🏆 Efficiency Leaderboard")

leaderboard = pd.DataFrame({
    "Model": ["Sonar","GPT","Gemini","Claude"],
    "Efficiency Score": np.round(100 - np.random.rand(4)*30, 2)
}).sort_values(by="Efficiency Score", ascending=False)

st.dataframe(leaderboard, use_container_width=True)

# ---------------- EXPORT ----------------
csv = st.session_state.data.to_csv(index=False).encode()
st.download_button("📁 Download Data", csv, "data.csv")
