# ================= STREAMLIT FRONTEND ONLY (ADVANCED, INTERACTIVE, ~250 LINES) =================
# Run: streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import plotly.express as px

# ---------------- CONFIG ----------------
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

# ---------------- STATE ----------------
if "running" not in st.session_state:
    st.session_state.running = False

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(20)),
        "queries": np.random.randint(20,120,20),
        "co2": np.random.randint(10,60,20),
        "power": np.random.randint(200,400,20)
    })

# ---------------- HEADER ----------------
st.title("⚡ AI Sustainability Monitoring Dashboard")

c1,c2,c3,c4 = st.columns(4)
latest = st.session_state.data.iloc[-1]

c1.metric("Queries", int(latest["queries"]))
c2.metric("CO2", f"{int(latest['co2'])} kg")
c3.metric("Power", f"{int(latest['power'])} kWh")
c4.metric("Model", model)

# ---------------- CONTROL PANEL ----------------
st.markdown("### 🎛️ Control Panel")
colA,colB,colC = st.columns(3)

with colA:
    if st.button("▶️ Start Monitoring"):
        st.session_state.running = True

with colB:
    if st.button("⏸ Stop Monitoring"):
        st.session_state.running = False

with colC:
    if st.button("🔄 Reset Data"):
        st.session_state.data = st.session_state.data.iloc[:20]

# ---------------- EXTRA CONTROLS ----------------
colD,colE,colF = st.columns(3)

with colD:
    if st.button("⚠️ Simulate CO2 Spike"):
        st.session_state.data.loc[st.session_state.data.index[-1],"co2"] = 95

with colE:
    if st.button("📉 Reduce Load"):
        st.session_state.data.loc[st.session_state.data.index[-1],"queries"] = 20

with colF:
    if st.button("⚡ Boost Traffic"):
        st.session_state.data.loc[st.session_state.data.index[-1],"queries"] = 150

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Real-Time","📊 Analytics","📈 Advanced","🧠 AI"
])

# ================= REAL-TIME TAB =================
with tab1:
    st.subheader("Live Monitoring System")

    chart = st.empty()
    alert = st.empty()

    if st.session_state.running:
        for i in range(200):
            new = {
                "time": st.session_state.data["time"].iloc[-1] + 1,
                "queries": np.random.randint(20,120),
                "co2": np.random.randint(10,100),
                "power": np.random.randint(200,400)
            }

            st.session_state.data = pd.concat([
                st.session_state.data,
                pd.DataFrame([new])
            ], ignore_index=True).tail(window)

            df = st.session_state.data
            latest = df.iloc[-1]

            # -------- ALERT LOGIC --------
            if latest["co2"] > threshold_warn:
                alert.error("🚨 HIGH CO2 LEVEL")
            elif latest["co2"] > threshold_safe:
                alert.warning("⚠️ Moderate CO2")
            else:
                alert.success("✅ System Stable")

            # -------- GRAPH --------
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=df["time"], y=df["co2"],
                name="CO2", mode="lines",
                line=dict(color="red", width=3)
            ))

            fig.add_trace(go.Scatter(
                x=df["time"], y=df["queries"],
                name="Queries", mode="lines",
                line=dict(color="blue")
            ))

            fig.add_trace(go.Scatter(
                x=df["time"], y=df["power"],
                name="Power", mode="lines",
                line=dict(color="green")
            ))

            # colored zones
            fig.add_hrect(y0=0, y1=threshold_safe, fillcolor="green", opacity=0.1)
            fig.add_hrect(y0=threshold_safe, y1=threshold_warn, fillcolor="yellow", opacity=0.1)
            fig.add_hrect(y0=threshold_warn, y1=120, fillcolor="red", opacity=0.1)

            fig.update_layout(title="Real-Time Monitoring", height=400)

            chart.plotly_chart(fig, use_container_width=True)

            time.sleep(1)

            if not st.session_state.running:
                break

# ================= ANALYTICS =================
with tab2:
    df = st.session_state.data

    st.subheader("Historical Trends")
    st.line_chart(df.set_index("time")[["queries","co2"]])

    st.subheader("Power Usage")
    st.area_chart(df.set_index("time")["power"])

    st.subheader("Model Distribution")
    dist = pd.DataFrame({
        "model":["Sonar","GPT","Gemini","Claude"],
        "usage": np.random.randint(10,60,4)
    })
    st.bar_chart(dist.set_index("model"))

# ================= ADVANCED =================
with tab3:
    df = st.session_state.data

    st.subheader("3D Analysis")
    fig3d = px.scatter_3d(df, x="time", y="queries", z="co2", color="power")
    st.plotly_chart(fig3d, use_container_width=True)

    st.subheader("Heatmap")
    heat = np.random.rand(10,10)
    fig_heat = go.Figure(data=go.Heatmap(z=heat))
    st.plotly_chart(fig_heat, use_container_width=True)

# ================= AI =================
with tab4:
    st.subheader("AI Insights")

    st.success(f"{model}: Reduce peak loads and optimize scheduling.")

    scenario = st.selectbox("Scenario", ["Peak","Normal","Optimized"])

    if scenario == "Peak":
        st.error("⚠️ High emissions expected")
    elif scenario == "Optimized":
        st.success("✅ Efficient system")

    query = st.text_area("Enter query")

    if st.button("Run Model"):
        st.info(f"{model} suggests batching and caching.")

# ---------------- DATA EXPORT ----------------
st.markdown("### 📁 Data Export")
csv = st.session_state.data.to_csv(index=False).encode()
st.download_button("Download CSV", csv, "data.csv")

# ---------------- FOOTER ----------------
st.write("\n\n")

# ================= END =================
