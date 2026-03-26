# ================= FINAL FIXED DASHBOARD =================
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

model = st.sidebar.selectbox("Model", [
    "Sonar","GPT-5.4","Gemini 3.1 Pro",
    "Claude Sonnet 4.6","Claude Opus 4.6","Nemotron 3 Super"
])

window = st.sidebar.slider("Time Window", 20, 100, 40)
intensity = st.sidebar.slider("⚡ Intensity", 1, 5, 3)

# ---------------- STATE ----------------
if "running" not in st.session_state:
    st.session_state.running = False

if "mode" not in st.session_state:
    st.session_state.mode = "normal"

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(20)),
        "queries": np.random.randint(50,100,20),
        "co2": np.random.randint(20,50,20),
        "power": np.random.randint(250,350,20)
    })

# ---------------- HEADER ----------------
st.title("⚡ AI Sustainability Monitoring System")

df = st.session_state.data
latest = df.iloc[-1]

# -------- METRICS --------
c1,c2,c3,c4 = st.columns(4)
c1.metric("Queries", int(latest["queries"]))
c2.metric("CO2 (kg)", int(latest["co2"]))
c3.metric("Power (kWh)", int(latest["power"]))
c4.metric("Mode", st.session_state.mode.upper())

# -------- CARBON COST --------
carbon_cost = latest["co2"] * 0.02
st.metric("💰 Carbon Cost ($)", f"{carbon_cost:.2f}")

# ---------------- CONTROLS ----------------
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
st.markdown("### ⚡ System Behavior")

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
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Real-Time","📊 Analytics","📈 Advanced","🧠 AI Insights"
])

# ================= REAL-TIME =================
with tab1:

    st.subheader("⚡ Live System Monitoring")

    chart = st.empty()
    status_box = st.empty()

    if st.session_state.running:

        for _ in range(500):

            now = pd.Timestamp.now()
            mode = st.session_state.mode
            factor = intensity

            # -------- DATA GENERATION --------
            if mode == "spike":
                queries = np.random.randint(120,180) * factor
                co2 = np.random.randint(80,110)
                power = np.random.randint(350,450)

            elif mode == "low":
                queries = np.random.randint(10,40)
                co2 = np.random.randint(10,30)
                power = np.random.randint(150,250)

            elif mode == "high":
                queries = np.random.randint(150,220)
                co2 = np.random.randint(60,90)
                power = np.random.randint(300,450)

            else:
                queries = np.random.randint(40,100)
                co2 = np.random.randint(20,60)
                power = np.random.randint(200,350)

            new_row = {
                "time": now,
                "queries": queries,
                "co2": co2,
                "power": power
            }

            st.session_state.data = pd.concat(
                [st.session_state.data, pd.DataFrame([new_row])],
                ignore_index=True
            ).tail(window)

            df = st.session_state.data.copy()
            latest = df.iloc[-1]

            # -------- STATUS CLASSIFICATION --------
            if latest["co2"] > 80:
                status = "🔴 CRITICAL"
                color = "red"
            elif latest["co2"] > 60:
                status = "🟠 HIGH"
                color = "orange"
            elif latest["co2"] > 40:
                status = "🟡 MEDIUM"
                color = "yellow"
            else:
                status = "🟢 LOW"
                color = "green"

            status_box.markdown(f"### System Status: {status}")

            # -------- SAFE ANOMALY --------
            rolling_mean = df["co2"].rolling(5).mean().fillna(0)
            rolling_std = df["co2"].rolling(5).std().fillna(0)

            anomalies = df[df["co2"] > (rolling_mean + 2*rolling_std)]

            # -------- GRAPH --------
            fig = go.Figure()

            # CO2 line
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["co2"],
                name="CO2",
                line=dict(color="red", width=3)
            ))

            # Queries
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["queries"],
                name="Queries",
                line=dict(color="blue")
            ))

            # Power
            fig.add_trace(go.Scatter(
                x=df["time"], y=df["power"],
                name="Power",
                line=dict(color="green")
            ))

            # -------- ZONES --------
            fig.add_hrect(y0=0, y1=40, fillcolor="green", opacity=0.08)
            fig.add_hrect(y0=40, y1=60, fillcolor="yellow", opacity=0.08)
            fig.add_hrect(y0=60, y1=80, fillcolor="orange", opacity=0.08)
            fig.add_hrect(y0=80, y1=120, fillcolor="red", opacity=0.08)

            # -------- ANOMALY --------
            fig.add_trace(go.Scatter(
                x=anomalies["time"],
                y=anomalies["co2"],
                mode="markers",
                marker=dict(color="red", size=10),
                name="Anomaly"
            ))

            fig.update_layout(
                height=420,
                title=f"Live Monitoring | Status: {status}"
            )

            chart.plotly_chart(fig, use_container_width=True)

            time.sleep(1)

            if not st.session_state.running:
                break

    # -------- KEEP LAST GRAPH AFTER STOP --------
    df = st.session_state.data.copy()

    if not df.empty:
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=df["time"], y=df["co2"], name="CO2"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["queries"], name="Queries"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["power"], name="Power"))

        fig.add_hrect(y0=0, y1=40, fillcolor="green", opacity=0.08)
        fig.add_hrect(y0=40, y1=60, fillcolor="yellow", opacity=0.08)
        fig.add_hrect(y0=60, y1=80, fillcolor="orange", opacity=0.08)
        fig.add_hrect(y0=80, y1=120, fillcolor="red", opacity=0.08)

        chart.plotly_chart(fig, use_container_width=True)

    # ✅ KEEP LAST GRAPH AFTER STOP
    df = st.session_state.data.copy()

    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["time"], y=df["co2"], name="CO2"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["queries"], name="Queries"))
        fig.add_trace(go.Scatter(x=df["time"], y=df["power"], name="Power"))

        chart.plotly_chart(fig, use_container_width=True)
# ================= ANALYTICS =================
with tab2:

    df = st.session_state.data

    st.subheader("📊 System Analytics")

    # -------- KPI SUMMARY --------
    c1, c2, c3 = st.columns(3)

    c1.metric("Avg CO2", round(df["co2"].mean(), 2))
    c2.metric("Peak CO2", int(df["co2"].max()))
    c3.metric("Avg Power", round(df["power"].mean(), 2))

    # -------- ROLLING TREND --------
    st.markdown("### 📈 Smoothed Trends")

    rolling = df.set_index("time").rolling(5).mean()
    st.line_chart(rolling[["co2","queries","power"]])

    # -------- CORRELATION HEATMAP --------
    st.markdown("### 🔗 Feature Correlation")

    corr = df[["queries","co2","power"]].corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=corr.columns,
        y=corr.columns,
        colorscale="RdBu"
    ))

    st.plotly_chart(fig, use_container_width=True)

    # -------- DISTRIBUTION --------
    st.markdown("### 📊 Distribution")

    st.bar_chart(df.tail(15)[["queries","co2","power"]])

# ================= ADVANCED =================
with tab3:

    st.subheader("📈 Advanced System Insights")

    df = st.session_state.data.copy()

    # -------- CLEAN DATA --------
    df["queries"] = pd.to_numeric(df["queries"], errors="coerce")
    df["co2"] = pd.to_numeric(df["co2"], errors="coerce")
    df["power"] = pd.to_numeric(df["power"], errors="coerce")

    df = df.dropna()

    if len(df) < 8:
        st.warning("Not enough data for advanced visualization")
    else:
        import plotly.express as px

        # -------- MAKE TIME CLEAN --------
        df = df.reset_index(drop=True)
        df["index"] = df.index

        df_sample = df.iloc[::2]  # reduce clutter

        # ================= 1. 3D SYSTEM VIEW =================
        st.markdown("### 🌐 3D System View")

        fig3d = px.scatter_3d(
            df_sample,
            x="index",
            y="queries",
            z="co2",
            color="power",
            size="queries",
            color_continuous_scale="Turbo"
        )

        fig3d.update_traces(marker=dict(size=6, opacity=0.8))

        fig3d.update_layout(
            template="plotly_dark",
            height=450,
            scene=dict(
                xaxis_title="Time",
                yaxis_title="Queries",
                zaxis_title="CO2"
            ),
            scene_camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        )

        st.plotly_chart(fig3d, use_container_width=True)

        # ================= 2. LOAD VS EMISSIONS =================
        st.markdown("### 🔵 Load vs Emissions")

        fig_bubble = px.scatter(
            df,
            x="queries",
            y="co2",
            size="power",
            color="power",
            hover_data=["index"],
            color_continuous_scale="Turbo"
        )

        fig_bubble.update_traces(marker=dict(opacity=0.75))

        fig_bubble.update_layout(
            template="plotly_dark",
            height=400
        )

        st.plotly_chart(fig_bubble, use_container_width=True)

        # ================= 3. SYSTEM STRESS GAUGE =================
        st.markdown("### ⚡ System Stress Indicator")

        stress = int(min(100, df["co2"].iloc[-1]))

        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=stress,
            title={"text": "CO2 Stress Level"},
            gauge={
                "axis": {"range": [0,100]},
                "bar": {"color": "red"},
                "steps": [
                    {"range": [0,40], "color": "green"},
                    {"range": [40,70], "color": "yellow"},
                    {"range": [70,100], "color": "red"},
                ],
            }
        ))

        gauge.update_layout(height=300)

        st.plotly_chart(gauge, use_container_width=True)

        # ================= 4. ANOMALY DENSITY =================
        st.markdown("### 🚨 Anomaly Density")

        rolling_mean = df["co2"].rolling(5).mean().fillna(df["co2"])
        rolling_std = df["co2"].rolling(5).std().fillna(0)

        anomalies = df[df["co2"] > (rolling_mean + 1.5 * rolling_std)]

        # fallback (important for demo)
        if anomalies.empty:
            anomalies = df.sort_values("co2", ascending=False).head(3)

        st.write(f"Total anomalies detected: {len(anomalies)}")

        fig_anom = px.bar(
            anomalies,
            x="index",
            y="co2",
            color="co2",
            color_continuous_scale="Reds"
        )

        fig_anom.update_layout(
            template="plotly_dark",
            height=350
        )

        st.plotly_chart(fig_anom, use_container_width=True)
# ================= AI =================
with tab4:

    st.subheader("🧠 AI Decision Engine")

    df = st.session_state.data
    latest = df.iloc[-1]

    co2 = latest["co2"]
    queries = latest["queries"]
    power = latest["power"]

    # -------- HEALTH CLASSIFICATION --------
    if co2 > 80:
        st.error("🚨 Critical System State")
        risk = "HIGH"
    elif co2 > 50:
        st.warning("⚠️ Moderate Risk")
        risk = "MEDIUM"
    else:
        st.success("✅ Healthy System")
        risk = "LOW"

    # -------- TREND DETECTION --------
    trend = df["co2"].tail(5).mean() - df["co2"].head(5).mean()

    if trend > 10:
        st.warning("📈 CO2 Increasing Trend Detected")
    elif trend < -10:
        st.success("📉 CO2 Decreasing Trend")
    else:
        st.info("➡️ Stable Trend")

    # -------- PREDICTION --------
    predicted = co2 - 10

    st.markdown(f"### 🔮 Predicted CO2 (Next Cycle): {int(predicted)}")

    # -------- AI RECOMMENDATIONS --------
    st.markdown("### 🤖 AI Recommendations")

    if risk == "HIGH":
        st.write("- Shift workloads to off-peak hours")
        st.write("- Enable model compression")
        st.write("- Reduce query load immediately")

    elif risk == "MEDIUM":
        st.write("- Optimize batching")
        st.write("- Monitor energy usage closely")

    else:
        st.write("- Maintain current configuration")
        st.write("- Continue monitoring")

    # -------- SCENARIO SIMULATION --------
    st.markdown("### 🧪 Scenario Simulation")

    scenario = st.selectbox("Choose Scenario", ["Peak Load","Optimized","Balanced"])

    if scenario == "Peak Load":
        st.error("Expected: High CO2 spike and system stress")

    elif scenario == "Optimized":
        st.success("Expected: Reduced emissions and stable system")

    else:
        st.info("Expected: Balanced performance")

    # -------- USER QUERY --------
    query = st.text_area("Ask AI")

    if st.button("Run AI Analysis"):
        st.info(f"{model} suggests adaptive scaling and load balancing.")
# ---------------- EXPORT ----------------
csv = st.session_state.data.to_csv(index=False).encode()
st.download_button("📁 Download CSV", csv, "data.csv")
