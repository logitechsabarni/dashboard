import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.express as px
import plotly.graph_objects as go

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Sustainability Dashboard", layout="wide")

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Controls")
model = st.sidebar.selectbox("Select Model", ["Sonar","GPT-5.4","Gemini 3.1 Pro","Claude Sonnet 4.6","Claude Opus 4.6","Nemotron 3 Super"])
window = st.sidebar.slider("Time Window", 10, 100, 30)
live_toggle = st.sidebar.toggle("⚡ Live Monitoring", value=True)
threshold = st.sidebar.slider("CO2 Threshold", 10, 100, 50)

# ---------------- DATA INIT ----------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "time": list(range(10)),
        "queries": np.random.randint(20,120,10),
        "co2": np.random.randint(10,60,10),
        "power": np.random.randint(200,400,10)
    })

# ---------------- STREAM FUNCTION ----------------
def websocket_stream():
    return {
        "time": st.session_state.data["time"].iloc[-1] + 1,
        "queries": np.random.randint(20,120),
        "co2": np.random.randint(10,60),
        "power": np.random.randint(200,400)
    }

# ---------------- LIVE UPDATE ----------------
if live_toggle:
    new = websocket_stream()
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new])], ignore_index=True)
    st.session_state.data = st.session_state.data.tail(window)

latest = st.session_state.data.iloc[-1]

# ---------------- HEADER ----------------
c1,c2,c3,c4 = st.columns(4)
c1.metric("Queries", int(latest["queries"]))
c2.metric("CO2", f"{int(latest['co2'])} kg")
c3.metric("Power", f"{int(latest['power'])} kWh")
c4.metric("Model", model)

# ---------------- ALERT ----------------
if latest["co2"] > threshold:
    st.error("🚨 High CO2 Emission Detected!")

# ---------------- EXTRA CONTROLS ----------------
st.markdown("### 🎛️ Simulation Controls")
cA,cB,cC = st.columns(3)
with cA:
    if st.button("⚠️ Simulate Spike"):
        st.session_state.data.loc[st.session_state.data.index[-1],"co2"] = 95
with cB:
    if st.button("📉 Drop Load"):
        st.session_state.data.loc[st.session_state.data.index[-1],"queries"] = 20
with cC:
    if st.button("🔄 Reset"):
        st.session_state.data = st.session_state.data.iloc[:10]

# ---------------- TABS ----------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics","📈 Advanced","🧠 AI","📁 Data"])

# -------- TAB 1 --------
with tab1:
    df = st.session_state.data

    fig1 = px.line(df, x="time", y="queries", title="Live Queries", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(df, x="time", y=["queries","co2"], title="CO2 vs Queries")
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.area(df, x="time", y="power", title="Power Consumption")
    st.plotly_chart(fig3, use_container_width=True)

# -------- TAB 2 (ADVANCED VISUALS) --------
with tab2:
    st.subheader("3D Visualization")
    fig4 = px.scatter_3d(df, x="time", y="queries", z="co2", color="power")
    st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Heatmap")
    heat = np.random.rand(10,10)
    fig5 = go.Figure(data=go.Heatmap(z=heat))
    st.plotly_chart(fig5, use_container_width=True)

# -------- TAB 3 --------
with tab3:
    st.subheader("AI Insights")
    st.success(f"{model}: Optimize batching, reduce redundant queries, shift workloads.")

    scenario = st.selectbox("Scenario", ["Peak","Normal","Optimized"])
    if scenario == "Peak": st.warning("High emissions expected")
    elif scenario == "Optimized": st.success("Efficient system")

    query = st.text_area("Enter query")
    if st.button("Run Model"):
        st.info(f"{model} suggests caching + batching.")

# -------- TAB 4 --------
with tab4:
    st.dataframe(st.session_state.data, use_container_width=True)
    csv = st.session_state.data.to_csv(index=False).encode()
    st.download_button("Download CSV", csv, "data.csv")

# ---------------- LOOP ----------------
if live_toggle:
    time.sleep(1)
    st.rerun()

# ---------------- FOOTER ----------------
st.write("\n\n")

# Run: streamlit run filename.py
