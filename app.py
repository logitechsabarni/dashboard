# ================= ULTIMATE FINAL DASHBOARD =================
# streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")

model = st.sidebar.selectbox("Select Model", [
    "Sonar","GPT-5.4","Gemini 3.1 Pro",
    "Claude Sonnet 4.6","Claude Opus 4.6","Nemotron 3 Super"
])

window = st.sidebar.slider("Time Window", 20, 100, 40)
threshold_safe = st.sidebar.slider("Safe Limit", 10, 60, 40)
threshold_warn = st.sidebar.slider("Warning Limit", 40, 100, 70)
intensity = st.sidebar.slider("⚡ Intensity", 1, 5, 3)

# ---------------- STATE ----------------
if "running" not in st.session_state:
    st.session_state.running = False

if "mode" not in st.session_state:
    st.session_state.mode = "normal"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(20)),
        "queries": np.random.randint(20,120,20),
        "co2": np.random.randint(10,60,20),
        "power": np.random.randint(200,400,20)
    })

# ---------------- HEADER ----------------
st.title("⚡ AI Sustainability Monitoring Dashboard")

latest = st.session_state.data.iloc[-1]

c1,c2,c3,c4 = st.columns(4)
c1.metric("Queries", int(latest["queries"]))
c2.metric("CO2", f"{int(latest['co2'])} kg")
c3.metric("Power", f"{int(latest['power'])} kWh")
c4.metric("Mode", st.session_state.mode.upper())

# ---------------- CONTROL PANEL ----------------
st.markdown("### 🎛️ Controls")

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
st.markdown("### ⚡ Behavior Controls")

b1,b2,b3,b4 = st.columns(4)

with b1:
    if st.button("⚠️ Spike"):
        st.session_state.mode = "spike"

with b2:
    if st.button("📉 Reduce"):
        st.session_state.mode = "low"

with b3:
    if st.button("🚀 Boost"):
        st.session_state.mode = "high"

with b4:
    if st.button("✅ Normal"):
        st.session_state.mode = "normal"

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Real-Time","📊 Analytics","📈 Advanced","🧠 AI"])

# ================= REAL-TIME =================
with tab1:

    chart = st.empty()
    alert = st.empty()

    if st.session_state.running:
        for _ in range(500):

            mode = st.session_state.mode
            factor = intensity

            if mode == "spike":
                queries = np.random.randint(100,150) * factor
                co2 = np.random.randint(70,100)
                power = np.random.randint(350,450)

            elif mode == "low":
                queries = np.random.randint(10,40) // factor
                co2 = np.random.randint(10,30)
                power = np.random.randint(150,250)

            elif mode == "high":
                queries = np.random.randint(120,180) * factor
                co2 = np.random.randint(60,90)
                power = np.random.randint(300,450)

            else:
                queries = np.random.randint(40,100)
                co2 = np.random.randint(20,60)
                power = np.random.randint(200,350)

            new = {
                "time": st.session_state.data["time"].iloc[-1] + 1,
                "queries": queries,
                "co2": co2,
                "power": power
            }

            st.session_state.data = pd.concat([
                st.session_state.data,
                pd.DataFrame([new])
            ], ignore_index=True).tail(window)

            df = st.session_state.data
            latest = df.iloc[-1]

            # -------- ML ANOMALY DETECTION --------
            rolling_mean = df["co2"].rolling(5).mean()
            rolling_std = df["co2"].rolling(5).std()

            anomalies = df[
                df["co2"] > (rolling_mean + 2*rolling_std)
            ]

            # -------- CARBON COST --------
            carbon_cost = latest["co2"] * 0.02

            # -------- ALERT --------
            if len(anomalies) > 0:
                alert.error(f"🚨 ML Anomaly Detected | Cost: ${carbon_cost:.2f}")
            elif latest["co2"] > threshold_warn:
                alert.warning(f"⚠️ High CO2 | Cost: ${carbon_cost:.2f}")
            else:
                alert.success(f"✅ Stable | Cost: ${carbon_cost:.2f}")

            # -------- PREDICTION --------
            future_x = np.arange(df["time"].iloc[-1], df["time"].iloc[-1]+10)
            future_y = np.linspace(latest["co2"], latest["co2"]-10, 10)

            # -------- GRAPH --------
            fig = go.Figure()

            fig.add_trace(go.Scatter(x=df["time"], y=df["co2"], name="CO2", line=dict(color="red", width=3)))
            fig.add_trace(go.Scatter(x=df["time"], y=df["queries"], name="Queries", line=dict(color="blue")))
            fig.add_trace(go.Scatter(x=df["time"], y=df["power"], name="Power", line=dict(color="green")))

            fig.add_trace(go.Scatter(
                x=anomalies["time"],
                y=anomalies["co2"],
                mode="markers",
                marker=dict(color="red", size=10),
                name="ML Anomaly"
            ))

            fig.add_trace(go.Scatter(
                x=future_x,
                y=future_y,
                mode="lines",
                line=dict(dash="dash"),
                name="Prediction"
            ))

            fig.add_hrect(y0=0, y1=threshold_safe, fillcolor="green", opacity=0.1)
            fig.add_hrect(y0=threshold_safe, y1=threshold_warn, fillcolor="yellow", opacity=0.1)
            fig.add_hrect(y0=threshold_warn, y1=120, fillcolor="red", opacity=0.1)

            chart.plotly_chart(fig, use_container_width=True)

            time.sleep(1)

            if not st.session_state.running:
                break

# ================= ANALYTICS =================
with tab2:
    df = st.session_state.data

    st.line_chart(df.set_index("time")[["queries","co2"]])
    st.area_chart(df.set_index("time")["power"])

    # -------- LEADERBOARD --------
    st.subheader("🏆 Model Efficiency Leaderboard")

    leaderboard = pd.DataFrame({
        "Model": ["Sonar","GPT","Gemini","Claude"],
        "Score": np.random.randint(70,100,4)
    }).sort_values(by="Score", ascending=False)

    st.table(leaderboard)

# ================= ADVANCED =================
with tab3:
    df = st.session_state.data

    fig3d = px.scatter_3d(df, x="time", y="queries", z="co2", color="power")
    st.plotly_chart(fig3d, use_container_width=True)

    heat = np.random.rand(10,10)
    st.plotly_chart(go.Figure(data=go.Heatmap(z=heat)))

# ================= AI =================
with tab4:
    st.success(f"{model}: Optimize workloads to reduce emissions.")

# ---------------- EXPORT ----------------
csv = st.session_state.data.to_csv(index=False).encode()
st.download_button("Download CSV", csv, "data.csv")
