// ============================================================
// AI SUSTAINABILITY DASHBOARD v5 — Premium React SaaS Edition
// All logic from v4 preserved. Enhanced UI/UX only.
// ============================================================

import { useState, useEffect, useRef, useCallback } from "react";
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine, Cell
} from "recharts";

// ─────────────────────────────────────────────
// CONFIG  (mirrors Python MODEL_SPECS exactly)
// ─────────────────────────────────────────────
const MODEL_SPECS = {
  "Claude Sonnet 4.6": { co2: 0.30, power: 1.5, efficiency: 0.88, color: "#38bdf8" },
  "Claude Opus 4.6":   { co2: 0.55, power: 2.8, efficiency: 0.75, color: "#a78bfa" },
  "GPT-5.4":           { co2: 0.50, power: 2.5, efficiency: 0.78, color: "#f472b6" },
  "Gemini 3.1 Pro":    { co2: 0.42, power: 2.1, efficiency: 0.82, color: "#34d399" },
  "Sonar":             { co2: 0.22, power: 1.1, efficiency: 0.92, color: "#fbbf24" },
  "Nemotron 3 Super":  { co2: 0.60, power: 3.0, efficiency: 0.70, color: "#fb923c" },
};

const CARBON_PRICE   = 0.02;
const TREE_ABS_YR    = 21.77;
const SLEEP_MS       = 700;
const ALERT_COOLDOWN = { CRITICAL: 3, HIGH: 5, MEDIUM: 8 };

// ─── Threshold defaults — lower so alerts fire readily
const DEFAULT_CRIT = 55, DEFAULT_HIGH = 38, DEFAULT_MED = 22;

// ─── SVG Icons (inline, zero deps)
const Icons = {
  Leaf: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.5.4 7.8C18.1 12.3 17 14 14 16.4L13 20z"/>
      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>
    </svg>
  ),
  Zap: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  ),
  Cloud: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>
    </svg>
  ),
  Activity: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  ),
  Tree: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M17 14l-5-5-5 5h3v6h4v-6z"/><path d="M17 9l-5-5-5 5h3"/>
    </svg>
  ),
  AlertTriangle: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  TrendingUp: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
      <polyline points="17 6 23 6 23 12"/>
    </svg>
  ),
  TrendingDown: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
      <polyline points="17 18 23 18 23 12"/>
    </svg>
  ),
  Download: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  ),
  Sun: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <circle cx="12" cy="12" r="5"/>
      <line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/>
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
      <line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
    </svg>
  ),
  Moon: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:"100%",height:"100%"}}>
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>
  ),
};

// ─── Utility: initial data
function freshData() {
  return Array.from({ length: 20 }, (_, i) => {
    const q = 60 + Math.random() * 70;
    return { tick: i, queries: Math.round(q), co2: +(q * 0.32 * (1 + (Math.random()-.5)*.3)).toFixed(1), power: +(q * 1.6 * (1 + (Math.random()-.5)*.2)).toFixed(1) };
  });
}

// ─── Utility: Holt's linear forecast
function linearForecast(series, steps = 8) {
  if (series.length < 3) return Array(steps).fill(series[series.length - 1] || 0);
  const [alpha, beta] = [0.4, 0.2];
  let level = series[0], trend = series[1] - series[0];
  for (const v of series.slice(1)) {
    const pl = level;
    level = alpha * v + (1 - alpha) * (level + trend);
    trend = beta * (level - pl) + (1 - beta) * trend;
  }
  return Array.from({ length: steps }, (_, i) => Math.max(0, +(level + (i + 1) * trend).toFixed(1)));
}

// ─── Utility: efficiency score
function calcEfficiency(data, modelKey) {
  const spec = MODEL_SPECS[modelKey];
  const avgCo2 = data.reduce((s, d) => s + d.co2, 0) / Math.max(data.length, 1);
  const avgQ   = data.reduce((s, d) => s + d.queries, 0) / Math.max(data.length, 1);
  const raw    = 1 - (avgCo2 / Math.max(avgQ, 1)) / spec.co2;
  return Math.max(0, Math.min(100, raw * 100 * spec.efficiency)).toFixed(1);
}

// ─── Utility: get status
function getStatus(co2, crit, high, med) {
  if (co2 > crit) return { label: "🔴 CRITICAL", color: "#f87171", cls: "critical" };
  if (co2 > high) return { label: "🟠 HIGH",     color: "#fb923c", cls: "high" };
  if (co2 > med)  return { label: "🟡 MEDIUM",   color: "#fbbf24", cls: "medium" };
  return { label: "🟢 LOW", color: "#34d399", cls: "low" };
}

function treesNeeded(co2) { return (co2 / TREE_ABS_YR).toFixed(2); }
function carbonCost(co2)  { return (co2 * CARBON_PRICE).toFixed(2); }

// ─── Custom Recharts Tooltip
const CustomTooltip = ({ active, payload, label, dark }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: dark ? "rgba(17,24,39,.95)" : "rgba(255,255,255,.97)",
      border: `1px solid ${dark?"#243049":"#d0d5e8"}`,
      borderRadius: 10, padding: "10px 14px",
      fontFamily: "'JetBrains Mono',monospace", fontSize: 12,
      boxShadow: "0 8px 32px rgba(0,0,0,.35)",
    }}>
      <div style={{ color: dark?"#4b5a72":"#94a3b8", marginBottom: 6, fontSize: 10, letterSpacing: ".1em", textTransform:"uppercase" }}>
        Tick #{label}
      </div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display:"flex", gap: 8, alignItems:"center", marginBottom:3 }}>
          <span style={{ width:8, height:8, borderRadius:"50%", background:p.color, display:"inline-block" }}/>
          <span style={{ color: dark?"#e2e8f0":"#1a2035" }}>{p.name}:</span>
          <strong>{typeof p.value === "number" ? p.value.toFixed(1) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

// ─── Toast notification component
function Toast({ toasts, onRemove }) {
  return (
    <div style={{ position:"fixed", top:20, right:20, zIndex:9999, display:"flex", flexDirection:"column", gap:8 }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          background: t.level==="CRITICAL" ? "rgba(248,113,113,.15)" : t.level==="HIGH" ? "rgba(251,146,60,.13)" : "rgba(251,191,36,.12)",
          border: `1px solid ${t.level==="CRITICAL"?"rgba(248,113,113,.6)":t.level==="HIGH"?"rgba(251,146,60,.5)":"rgba(251,191,36,.45)"}`,
          borderRadius: 12, padding: "12px 16px",
          fontFamily:"'JetBrains Mono',monospace", fontSize:13,
          color: t.level==="CRITICAL"?"#f87171":t.level==="HIGH"?"#fb923c":"#fbbf24",
          backdropFilter:"blur(16px)",
          boxShadow: t.level==="CRITICAL" ? "0 0 20px rgba(248,113,113,.25)":"0 4px 20px rgba(0,0,0,.3)",
          animation:"slideInRight .3s ease",
          cursor:"pointer", maxWidth:340,
          display:"flex", alignItems:"center", gap:10,
        }} onClick={() => onRemove(t.id)}>
          <span style={{ fontSize:16 }}>{t.level==="CRITICAL"?"🚨":t.level==="HIGH"?"⚠️":"🟡"}</span>
          <div>
            <div style={{ fontWeight:700, fontSize:11, letterSpacing:".08em", marginBottom:2 }}>{t.level}</div>
            <div style={{ fontSize:12, opacity:.9 }}>{t.message}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Metric Card component
function MetricCard({ label, value, delta, icon: IconComp, iconColor, accent, dark, sub }) {
  const isPositive = delta > 0;
  const bg = dark ? "linear-gradient(135deg,#111827,#1a2236)" : "linear-gradient(135deg,#fff,#eef0f7)";
  const border = dark ? "#243049" : "#d0d5e8";
  return (
    <div style={{
      background: bg, border:`1px solid ${border}`,
      borderRadius:14, padding:"16px 18px",
      borderTop:`2px solid ${accent||"#38bdf8"}`,
      transition:"all .28s cubic-bezier(.4,0,.2,1)",
      position:"relative", overflow:"hidden",
      cursor:"default",
    }}
    onMouseEnter={e => { e.currentTarget.style.transform="translateY(-3px)"; e.currentTarget.style.boxShadow=`0 12px 32px rgba(56,189,248,.15)`; }}
    onMouseLeave={e => { e.currentTarget.style.transform=""; e.currentTarget.style.boxShadow=""; }}
    >
      {/* shimmer line */}
      <div style={{ position:"absolute",top:0,left:0,right:0,height:1,background:"linear-gradient(90deg,transparent,rgba(56,189,248,.4),transparent)" }}/>
      {/* bg icon watermark */}
      {IconComp && (
        <div style={{ position:"absolute",right:12,top:12,width:36,height:36,opacity:.08,color:iconColor||"#38bdf8" }}>
          <IconComp/>
        </div>
      )}
      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10.5,letterSpacing:".09em",textTransform:"uppercase",color:dark?"#4b5a72":"#94a3b8",marginBottom:6 }}>
        {label}
      </div>
      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"1.45rem",fontWeight:700,color:dark?"#e2e8f0":"#1a2035",lineHeight:1.1 }}>
        {value}
      </div>
      {delta !== undefined && (
        <div style={{ display:"flex",alignItems:"center",gap:4,marginTop:5,fontSize:12,fontFamily:"'JetBrains Mono',monospace" }}>
          <span style={{ color: isPositive?"#f87171":"#34d399",fontWeight:700,fontSize:14 }}>
            {isPositive ? "↑" : "↓"}
          </span>
          <span style={{ color: isPositive?"#f87171":"#34d399" }}>{Math.abs(delta)}</span>
          {sub && <span style={{ color:dark?"#4b5a72":"#94a3b8",fontSize:10,marginLeft:4 }}>{sub}</span>}
        </div>
      )}
    </div>
  );
}

// ─── Score card
function ScoreCard({ label, value, detail, dark }) {
  const col = value >= 75 ? "#34d399" : value >= 50 ? "#fbbf24" : value >= 25 ? "#fb923c" : "#f87171";
  return (
    <div style={{
      textAlign:"center", padding:"18px 12px",
      background: dark?"linear-gradient(135deg,#111827,#1a2236)":"linear-gradient(135deg,#fff,#eef0f7)",
      border:`1px solid ${dark?"#243049":"#d0d5e8"}`,
      borderRadius:14, transition:"all .25s ease",
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor="#38bdf8"; e.currentTarget.style.transform="translateY(-2px)"; e.currentTarget.style.boxShadow="0 8px 28px rgba(56,189,248,.12)"; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor=dark?"#243049":"#d0d5e8"; e.currentTarget.style.transform=""; e.currentTarget.style.boxShadow=""; }}
    >
      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"2rem",fontWeight:700,color:col,lineHeight:1 }}>{value}</div>
      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:9.5,letterSpacing:".12em",textTransform:"uppercase",color:dark?"#4b5a72":"#94a3b8",margin:"7px 0 6px" }}>{label}</div>
      <div style={{ background:dark?"#1a2236":"#eef0f7",borderRadius:5,height:6,overflow:"hidden",margin:"6px 0" }}>
        <div style={{ height:"100%",borderRadius:5,background:col,width:`${Math.min(100,value)}%`,transition:"width .4s ease" }}/>
      </div>
      <div style={{ fontSize:10,color:dark?"#4b5a72":"#94a3b8" }}>{detail}</div>
    </div>
  );
}

// ─── Alert log entry
function AlertEntry({ entry, dark }) {
  const cfg = {
    CRITICAL:{ color:"#f87171",icon:"🔴",cls:"critical" },
    HIGH:    { color:"#fb923c",icon:"🟠",cls:"high" },
    MEDIUM:  { color:"#fbbf24",icon:"🟡",cls:"medium" },
  };
  const { color, icon } = cfg[entry.level] || { color:"#38bdf8",icon:"ℹ️" };
  return (
    <div style={{
      display:"flex",alignItems:"flex-start",gap:12,padding:"12px 16px",
      borderRadius:10,margin:"5px 0",
      border:`1px solid ${dark?"#243049":"#d0d5e8"}`,
      background:dark?"linear-gradient(135deg,#111827,#1a2236)":"linear-gradient(135deg,#fff,#eef0f7)",
      fontFamily:"'JetBrains Mono',monospace",fontSize:12,
      transition:"all .18s ease",
      borderLeft:`3px solid ${color}`,
      cursor:"default",
    }}
    onMouseEnter={e => { e.currentTarget.style.transform="translateX(3px)"; e.currentTarget.style.borderColor="#38bdf8"; }}
    onMouseLeave={e => { e.currentTarget.style.transform=""; e.currentTarget.style.borderColor=dark?"#243049":"#d0d5e8"; e.currentTarget.style.borderLeft=`3px solid ${color}`; }}
    >
      <div style={{ width:30,height:30,borderRadius:"50%",background:"rgba(0,0,0,.3)",border:`1px solid ${color}`,display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,flexShrink:0 }}>{icon}</div>
      <div style={{ flex:1 }}>
        <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:3 }}>
          <span style={{ color,fontWeight:700,fontSize:12 }}>{entry.level}</span>
          <span style={{ color:dark?"#4b5a72":"#94a3b8",fontSize:10 }}>{entry.ts} · tick #{entry.tick}</span>
        </div>
        <div style={{ color:dark?"#e2e8f0":"#1a2035",fontSize:12 }}>{entry.message}</div>
        <div style={{ color:dark?"#4b5a72":"#94a3b8",fontSize:10,marginTop:3 }}>
          CO₂: <span style={{ color }}>{entry.co2} kg</span> · Model: {entry.model}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// MAIN DASHBOARD
// ─────────────────────────────────────────────
export default function Dashboard() {
  // ── Theme
  const [dark, setDark] = useState(true);

  // ── Model & thresholds
  const [model,       setModel]       = useState("Claude Sonnet 4.6");
  const [co2Critical, setCo2Critical] = useState(DEFAULT_CRIT);
  const [co2High,     setCo2High]     = useState(DEFAULT_HIGH);
  const [co2Medium,   setCo2Medium]   = useState(DEFAULT_MED);
  const [intensity,   setIntensity]   = useState(4);
  const [noiseLevel,  setNoiseLevel]  = useState(2);
  const [window_,     setWindow_]     = useState(50);

  // ── Simulation
  const [running,    setRunning]    = useState(false);
  const [simMode,    setSimMode]    = useState("normal");
  const [data,       setData]       = useState(freshData);
  const [tick,       setTick]       = useState(20);

  // ── Cumulative stats
  const [cumCo2,     setCumCo2]     = useState(0);
  const [cumPower,   setCumPower]   = useState(0);
  const [totalQ,     setTotalQ]     = useState(0);
  const [peakCo2,    setPeakCo2]    = useState(0);
  const [peakPower,  setPeakPower]  = useState(0);
  const [totalAlerts,setTotalAlerts]= useState(0);
  const [uptickTick, setUptickTick] = useState(0);
  const [sessionStart]              = useState(Date.now());

  // ── Alert system
  const [alertLog,        setAlertLog]        = useState([]);
  const [toasts,          setToasts]          = useState([]);
  const [lastAlertTick,   setLastAlertTick]   = useState({ CRITICAL:-99, HIGH:-99, MEDIUM:-99 });
  const [sessionSnapshots,setSessionSnapshots]= useState([]);

  // ── UI state
  const [activeTab,  setActiveTab]  = useState("realtime");
  const [chatHistory,setChatHistory]= useState([]);
  const [chatInput,  setChatInput]  = useState("");
  const [aiLoading,  setAiLoading]  = useState(false);
  const [aiSummary,  setAiSummary]  = useState("");
  const [showForecast,  setShowForecast]  = useState(true);
  const [showAnomalies, setShowAnomalies] = useState(true);
  const [showThresholds,setShowThresholds]= useState(true);
  const [apiKey,     setApiKey]     = useState("");

  const runningRef  = useRef(running);
  const modeRef     = useRef(simMode);
  const tickRef     = useRef(tick);
  const lastATRef   = useRef(lastAlertTick);
  const uptickRef   = useRef(uptickTick);

  useEffect(() => { runningRef.current  = running;       }, [running]);
  useEffect(() => { modeRef.current     = simMode;       }, [simMode]);
  useEffect(() => { tickRef.current     = tick;          }, [tick]);
  useEffect(() => { lastATRef.current   = lastAlertTick; }, [lastAlertTick]);
  useEffect(() => { uptickRef.current   = uptickTick;    }, [uptickTick]);

  // ── Elapsed time
  const [elapsed, setElapsed] = useState("0:00:00");
  useEffect(() => {
    const iv = setInterval(() => {
      const s = Math.floor((Date.now() - sessionStart) / 1000);
      setElapsed(`${Math.floor(s/3600)}:${String(Math.floor((s%3600)/60)).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`);
    }, 1000);
    return () => clearInterval(iv);
  }, [sessionStart]);

  // ── Alert engine
  const tryLogAlert = useCallback((level, message, co2Val) => {
    const t = uptickRef.current;
    const cooldown = ALERT_COOLDOWN[level] || 5;
    const last = lastATRef.current[level] ?? -99;
    if (t - last < cooldown) return false;
    setLastAlertTick(prev => ({ ...prev, [level]: t }));
    const entry = { ts: new Date().toLocaleTimeString(), level, message, co2: +co2Val.toFixed(1), model, tick: t, id: Date.now() };
    setAlertLog(prev => [entry, ...prev].slice(0, 300));
    setTotalAlerts(n => n + 1);
    setToasts(prev => [...prev, { ...entry, id: Date.now() + Math.random() }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== entry.id + 1)), 5000);
    return true;
  }, [model]);

  const removeToast = useCallback(id => setToasts(prev => prev.filter(t => t.id !== id)), []);

  // ── Simulation loop
  useEffect(() => {
    if (!running) return;
    const spec = MODEL_SPECS[model];
    const iv = setInterval(() => {
      if (!runningRef.current) { clearInterval(iv); return; }
      setData(prev => {
        const last = prev[prev.length - 1];
        let baseQ = last.queries + (Math.random() - .5) * 16 * (noiseLevel + 1);
        const mode = modeRef.current;
        if (mode === "spike")  baseQ += (70 + Math.random()*60) * (intensity/4);
        else if (mode === "low")    baseQ -= 15 + Math.random()*30;
        else if (mode === "high")   baseQ += (35 + Math.random()*55) * (intensity/4);
        else if (Math.random() < .12) baseQ += 25 + Math.random()*45;

        const queries = Math.round(Math.max(10, Math.min(300, baseQ)));
        const noise   = 1 + (Math.random() - .5) * .28;
        const co2     = +Math.max(3, Math.min(200, queries * spec.co2 * noise)).toFixed(1);
        const power   = +Math.max(40, Math.min(700, queries * spec.power * (1 + (Math.random()-.5)*.19))).toFixed(1);
        const t       = tickRef.current + 1;

        setTick(t); tickRef.current = t;
        setCumCo2(c  => c + co2);
        setCumPower(p => p + power);
        setTotalQ(q  => q + queries);
        setUptickTick(u => { uptickRef.current = u+1; return u+1; });

        setPeakCo2(p  => Math.max(p, co2));
        setPeakPower(p => Math.max(p, power));

        // Alert engine
        if (co2 > co2Critical)      tryLogAlert("CRITICAL", `CO₂ ${co2} kg breached critical (${co2Critical} kg)`, co2);
        else if (co2 > co2High)     tryLogAlert("HIGH",     `CO₂ ${co2} kg above high (${co2High} kg)`, co2);
        else if (co2 > co2Medium)   tryLogAlert("MEDIUM",   `CO₂ ${co2} kg above medium (${co2Medium} kg)`, co2);
        if (mode==="spike" && Math.random()<.35) tryLogAlert("HIGH",`Spike surge: ${queries} q/tick`,co2);

        // Snapshot
        if ((uptickRef.current) % 8 === 0) {
          setSessionSnapshots(s => [...s.slice(-59), { tick:uptickRef.current, co2, queries, power }]);
        }

        return [...prev, { tick:t, queries, co2, power }].slice(-window_);
      });
    }, SLEEP_MS);
    return () => clearInterval(iv);
  }, [running, model, intensity, noiseLevel, window_, co2Critical, co2High, co2Medium, tryLogAlert]);

  // ── Derived values
  const latest       = data[data.length - 1] || { queries:0, co2:0, power:0 };
  const prev         = data[data.length - 2] || latest;
  const avg5co2      = data.slice(-5).reduce((s,d)=>s+d.co2,0) / Math.min(5,data.length||1);
  const status       = getStatus(avg5co2, co2Critical, co2High, co2Medium);
  const eff          = +calcEfficiency(data, model);
  const forecast     = linearForecast(data.map(d=>d.co2), 8);
  const forecastData = forecast.map((v,i) => ({ tick: (data[data.length-1]?.tick||0)+i+1, co2Forecast:v, upper:+(v*1.12).toFixed(1), lower:+(v*.88).toFixed(1) }));

  // Anomaly detection
  const anomalies = data.map((d, i) => {
    if (i < 4) return null;
    const window5 = data.slice(i-4, i+1).map(x=>x.co2);
    const mean = window5.reduce((s,v)=>s+v,0)/5;
    const std  = Math.sqrt(window5.reduce((s,v)=>s+(v-mean)**2,0)/5);
    return d.co2 > mean + 2*std ? d : null;
  }).filter(Boolean);

  // Scorecard
  const avgCo2 = data.reduce((s,d)=>s+d.co2,0)/Math.max(data.length,1);
  const stdCo2 = Math.sqrt(data.reduce((s,d)=>s+(d.co2-avgCo2)**2,0)/Math.max(data.length,1));
  const stability = Math.max(0,Math.min(100,100-(stdCo2/Math.max(avgCo2,1))*80)).toFixed(1);
  const carbonInt = Math.max(0,Math.min(100,(1-avgCo2/Math.max(co2Critical*1.2,1))*100)).toFixed(1);
  const alertScore= Math.max(0,Math.min(100,(1-totalAlerts/Math.max(uptickTick,1)*8)*100)).toFixed(1);
  const overallScore = (+eff*.35 + +stability*.25 + +carbonInt*.25 + +alertScore*.15).toFixed(1);

  // Projections
  const tph = 3600000 / SLEEP_MS;
  const projDaily = +(avgCo2 * tph * 24).toFixed(1);
  const projWeekly  = +(projDaily * 7).toFixed(1);
  const projMonthly = +(projDaily * 30).toFixed(1);
  const projYearly  = +(projDaily * 365).toFixed(1);

  // Compare models
  const compareRows = Object.entries(MODEL_SPECS).map(([name,spec]) => ({
    name, co2: +(latest.queries * spec.co2).toFixed(1),
    power: +(latest.queries * spec.power).toFixed(1),
    eff:   +(spec.efficiency*100).toFixed(0),
    cost:  +(latest.queries * spec.co2 * CARBON_PRICE).toFixed(3),
  })).sort((a,b)=>a.co2-b.co2);

  // ── CSV export
  const exportCSV = () => {
    const rows = ["tick,queries,co2,power", ...data.map(d=>`${d.tick},${d.queries},${d.co2},${d.power}`)].join("\n");
    const a = Object.assign(document.createElement("a"),{ href:`data:text/csv;charset=utf-8,${encodeURIComponent(rows)}`, download:"sustainability_data.csv" });
    a.click();
  };
  const exportAlertCSV = () => {
    if (!alertLog.length) return;
    const rows = ["ts,level,message,co2,model,tick", ...alertLog.map(a=>`${a.ts},${a.level},"${a.message}",${a.co2},${a.model},${a.tick}`)].join("\n");
    const a = Object.assign(document.createElement("a"),{ href:`data:text/csv;charset=utf-8,${encodeURIComponent(rows)}`, download:"alert_log.csv" });
    a.click();
  };

  // ── AI chat
  const sendChat = async () => {
    if (!chatInput.trim() || !apiKey) return;
    const userMsg = chatInput.trim(); setChatInput(""); setAiLoading(true);
    setChatHistory(h => [...h, { role:"user", content:userMsg }]);
    try {
      const res = await fetch("https://api.anthropic.com/v1/messages",{
        method:"POST",
        headers:{"x-api-key":apiKey,"anthropic-version":"2023-06-01","content-type":"application/json"},
        body:JSON.stringify({ model:"claude-sonnet-4-20250514", max_tokens:512,
          system:"You are an AI sustainability expert. Be concise and actionable.",
          messages:[...chatHistory,{role:"user",content:`CO₂:${latest.co2}kg, Model:${model}, Status:${status.label}. Q:${userMsg}`}] }),
      });
      const d = await res.json();
      setChatHistory(h => [...h, { role:"assistant", content:d.content?.[0]?.text||"Error" }]);
    } catch(e) { setChatHistory(h => [...h, { role:"assistant", content:`Error: ${e.message}` }]); }
    finally { setAiLoading(false); }
  };

  // ── Reset
  const handleReset = () => {
    setData(freshData()); setRunning(false); setSimMode("normal"); setTick(20);
    setCumCo2(0); setCumPower(0); setTotalQ(0); setPeakCo2(0); setPeakPower(0);
    setTotalAlerts(0); setUptickTick(0); setAlertLog([]); setToasts([]); setSessionSnapshots([]);
    setLastAlertTick({ CRITICAL:-99, HIGH:-99, MEDIUM:-99 }); setChatHistory([]);
  };

  // ─────────────── Theme tokens ───────────────
  const T = {
    bg:      dark ? "#080b12"  : "#f0f2f8",
    bg2:     dark ? "#0d1117"  : "#e8ecf4",
    card:    dark ? "#111827"  : "#ffffff",
    surface: dark ? "#1a2236"  : "#eef0f7",
    border:  dark ? "#243049"  : "#d0d5e8",
    text:    dark ? "#e2e8f0"  : "#1a2035",
    muted:   dark ? "#4b5a72"  : "#94a3b8",
    accent:  "#38bdf8", green:"#34d399", yellow:"#fbbf24",
    orange:"#fb923c", red:"#f87171", purple:"#a78bfa",
  };

  const pill = (t) => ({
    display:"inline-flex", alignItems:"center", gap:6,
    background: dark?"linear-gradient(135deg,#1a2236,#111827)":"linear-gradient(135deg,#eef0f7,#fff)",
    border:`1px solid ${T.border}`, borderRadius:20, padding:"4px 14px",
    fontFamily:"'JetBrains Mono',monospace", fontSize:10.5, letterSpacing:".12em",
    textTransform:"uppercase", color:T.accent, marginBottom:12,
    boxShadow:"0 2px 8px rgba(0,0,0,.2)",
  });

  const btn = (variant="default") => ({
    fontFamily:"'JetBrains Mono',monospace", fontSize:12, letterSpacing:".04em",
    background: variant==="primary" ? "linear-gradient(135deg,#38bdf8,#0ea5e9)"
              : variant==="danger"  ? "rgba(248,113,113,.12)"
              : dark?"#1a2236":"#eef0f7",
    color: variant==="primary" ? "#000" : variant==="danger"?"#f87171" : T.text,
    border: variant==="primary" ? "none" : `1px solid ${variant==="danger"?"rgba(248,113,113,.4)":T.border}`,
    borderRadius:9, padding:"8px 18px", cursor:"pointer",
    transition:"all .2s ease", fontWeight: variant==="primary"?"700":"400",
  });

  const tabStyle = (id) => ({
    fontFamily:"'JetBrains Mono',monospace", fontSize:12, letterSpacing:".04em",
    border:"none", cursor:"pointer", borderRadius:8, padding:"8px 16px",
    background: activeTab===id ? "linear-gradient(135deg,#38bdf8,#0ea5e9)" : "transparent",
    color: activeTab===id ? "#000" : T.muted,
    fontWeight: activeTab===id ? "700" : "400",
    transition:"all .2s ease",
    boxShadow: activeTab===id ? "0 4px 12px rgba(56,189,248,.35)" : "none",
  });

  const sectionHead = (label) => <div style={pill()}>{label}</div>;

  const modeColor = { normal:T.green, spike:T.red, low:T.accent, high:T.orange }[simMode] || T.accent;

  // ── Grade
  const grade = +overallScore>=90?"A+":+overallScore>=80?"A":+overallScore>=70?"B":+overallScore>=60?"C":+overallScore>=50?"D":"F";
  const gradeColor = +overallScore>=75?T.green:+overallScore>=50?T.yellow:+overallScore>=25?T.orange:T.red;

  // ─────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────
  return (
    <div style={{ background:T.bg, minHeight:"100vh", color:T.text, fontFamily:"'Space Grotesk',sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:5px; } ::-webkit-scrollbar-track { background:${T.bg}; }
        ::-webkit-scrollbar-thumb { background:${T.border}; border-radius:3px; }
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.55;transform:scale(1.22)} }
        @keyframes glowRed { 0%,100%{box-shadow:0 0 6px rgba(248,113,113,.4)} 50%{box-shadow:0 0 24px rgba(248,113,113,.9)} }
        @keyframes slideInRight { from{transform:translateX(80px);opacity:0} to{transform:translateX(0);opacity:1} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes shimmer { 0%{background-position:-200% center} 100%{background-position:200% center} }
        .pulse-dot { animation:pulse 1.4s ease-in-out infinite; display:inline-block; width:8px; height:8px; border-radius:50%; }
        .glow-critical { animation:glowRed 1.8s ease-in-out infinite !important; }
        .fade-in { animation:fadeIn .4s ease; }
        input[type=range] { width:100%; accent-color:#38bdf8; cursor:pointer; }
        input[type=text],input[type=password],textarea { outline:none; }
        input[type=text]:focus,input[type=password]:focus,textarea:focus { border-color:#38bdf8 !important; box-shadow:0 0 0 3px rgba(56,189,248,.12) !important; }
        button:hover { opacity:.92; }
        select { outline:none; cursor:pointer; }
        .recharts-cartesian-grid-horizontal line, .recharts-cartesian-grid-vertical line { stroke:${T.border}; }
        .recharts-text { fill:${T.muted}; font-family:'JetBrains Mono',monospace; font-size:11px; }
      `}</style>

      {/* Toasts */}
      <Toast toasts={toasts} onRemove={removeToast}/>

      <div style={{ maxWidth:1440, margin:"0 auto", padding:"0 20px 40px" }}>

        {/* ══════════ HEADER ══════════ */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-end", padding:"20px 0 14px", borderBottom:`1px solid ${T.border}`, marginBottom:18 }}>
          <div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".18em",textTransform:"uppercase",color:T.muted,marginBottom:5 }}>
              AI Sustainability Monitor · v5
            </div>
            <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"1.65rem",fontWeight:700,color:T.accent,letterSpacing:"-.03em" }}>
              ⚡ Emissions Dashboard
            </div>
            <div style={{ height:1,background:`linear-gradient(90deg,transparent,${T.accent},${T.purple},transparent)`,marginTop:8,opacity:.5 }}/>
          </div>
          <div style={{ textAlign:"right",fontFamily:"'JetBrains Mono',monospace",fontSize:12,color:T.muted,display:"flex",flexDirection:"column",gap:3 }}>
            <div style={{ display:"flex",alignItems:"center",gap:7,justifyContent:"flex-end" }}>
              <span className="pulse-dot" style={{ background: running?T.green:T.muted }}/>
              <span style={{ color:running?T.green:T.muted,fontWeight:700,fontSize:11 }}>{running?"● STREAMING LIVE":"○  PAUSED"}</span>
            </div>
            <div>Model · <span style={{ color:MODEL_SPECS[model].color,fontWeight:700 }}>{model}</span></div>
            <div>Uptime · <span style={{ color:T.text }}>{elapsed}</span></div>
            <div>Mode · <span style={{ color:modeColor,fontWeight:700,textTransform:"uppercase" }}>{simMode}</span></div>
            <div>Alerts · <span style={{ color:totalAlerts>3?T.red:T.text }}>{totalAlerts} fired</span></div>
            <button onClick={()=>setDark(d=>!d)} style={{ ...btn(), marginTop:4,display:"flex",alignItems:"center",gap:6,padding:"5px 10px",fontSize:11 }}>
              <div style={{ width:14,height:14 }}>{dark?<Icons.Sun/>:<Icons.Moon/>}</div>
              {dark?"Light":"Dark"} Mode
            </button>
          </div>
        </div>

        {/* ══════════ METRIC ROWS ══════════ */}
        <div style={{ display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:10,marginBottom:10 }}>
          <MetricCard label="Queries / Tick" value={latest.queries} delta={latest.queries-prev.queries} icon={Icons.Activity} iconColor={T.accent} dark={dark} sub="q/t"/>
          <MetricCard label="CO₂ (kg)"       value={latest.co2}     delta={+(latest.co2-prev.co2).toFixed(1)} icon={Icons.Cloud}    iconColor={T.red}    dark={dark} accent={T.red} sub="kg"/>
          <MetricCard label="Power (kWh)"    value={latest.power}   delta={+(latest.power-prev.power).toFixed(1)} icon={Icons.Zap} iconColor={T.yellow} dark={dark} accent={T.yellow} sub="kWh"/>
          <MetricCard label="System Status"  value={status.label}   icon={Icons.AlertTriangle} iconColor={status.color} dark={dark} accent={status.color}/>
          <MetricCard label="Efficiency"     value={`${eff}/100`}   icon={Icons.TrendingUp} iconColor={T.green} dark={dark} accent={T.green}/>
          <MetricCard label="Carbon Cost"    value={`$${carbonCost(cumCo2)}`} icon={Icons.Leaf} iconColor={T.purple} dark={dark} accent={T.purple}/>
        </div>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:10,marginBottom:18 }}>
          <MetricCard label="🌳 Trees / yr"    value={treesNeeded(cumCo2)} icon={Icons.Tree}        iconColor={T.green}  dark={dark} accent={T.green}/>
          <MetricCard label="📦 Cumul. CO₂"   value={cumCo2.toFixed(1)}   icon={Icons.Cloud}       iconColor={T.red}    dark={dark} accent={T.red}/>
          <MetricCard label="⚡ Cumul. Power" value={cumPower.toFixed(1)} icon={Icons.Zap}         iconColor={T.yellow} dark={dark} accent={T.yellow}/>
          <MetricCard label="🏔️ Peak CO₂"     value={peakCo2.toFixed(1)} icon={Icons.TrendingUp}  iconColor={T.orange} dark={dark} accent={T.orange}/>
          <MetricCard label="🔔 Total Alerts" value={totalAlerts}         icon={Icons.AlertTriangle} iconColor={T.red}  dark={dark} accent={totalAlerts>3?T.red:T.muted}/>
        </div>

        {/* ══════════ CONTROLS ══════════ */}
        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:20 }}>
          <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:"16px 20px" }}>
            <div style={pill()}>▶ Simulation Control</div>
            <div style={{ display:"flex",gap:8 }}>
              <button style={{ ...btn("primary"),flex:1 }} onClick={()=>setRunning(true)}>▶ Start</button>
              <button style={{ ...btn(),flex:1 }} onClick={()=>setRunning(false)}>⏸ Pause</button>
              <button style={{ ...btn("danger"),flex:1 }} onClick={handleReset}>↺ Reset</button>
            </div>
          </div>
          <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:"16px 20px" }}>
            <div style={pill()}>⚙ System Behavior</div>
            <div style={{ display:"flex",gap:8 }}>
              {[["⚠️ Spike","spike"],["📉 Reduce","low"],["🚀 Boost","high"],["✅ Normal","normal"]].map(([lbl,m])=>(
                <button key={m} style={{ ...btn(), flex:1, borderColor:simMode===m?modeColor:T.border, color:simMode===m?modeColor:T.text }} onClick={()=>{ setSimMode(m); if(m==="spike") tryLogAlert("HIGH","Spike mode activated",latest.co2); if(m==="high") tryLogAlert("MEDIUM","Boost mode engaged",latest.co2); }}>
                  {lbl}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ══════════ SIDEBAR + MAIN ══════════ */}
        <div style={{ display:"grid",gridTemplateColumns:"240px 1fr",gap:16 }}>

          {/* ── SIDEBAR ── */}
          <div style={{ display:"flex",flexDirection:"column",gap:12 }}>
            <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
              <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".12em",textTransform:"uppercase",color:T.accent,marginBottom:10 }}>⚙ Configuration</div>

              <label style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10.5,color:T.muted,textTransform:"uppercase",letterSpacing:".08em",display:"block",marginBottom:4 }}>Model</label>
              <select value={model} onChange={e=>setModel(e.target.value)} style={{ width:"100%",background:dark?"#1a2236":"#eef0f7",border:`1px solid ${T.border}`,borderRadius:8,padding:"7px 10px",color:T.text,fontFamily:"'JetBrains Mono',monospace",fontSize:12,marginBottom:10 }}>
                {Object.keys(MODEL_SPECS).map(m=><option key={m}>{m}</option>)}
              </select>
              <div style={{ display:"flex",alignItems:"center",gap:6,fontSize:11,fontFamily:"'JetBrains Mono',monospace",color:T.muted,marginBottom:14 }}>
                <span style={{ width:9,height:9,borderRadius:"50%",background:MODEL_SPECS[model].color,display:"inline-block",flexShrink:0 }}/>
                CO₂ factor: {MODEL_SPECS[model].co2} · Eff: {Math.round(MODEL_SPECS[model].efficiency*100)}%
              </div>

              {[["Query Intensity",intensity,setIntensity,1,10],["Noise Level",noiseLevel,setNoiseLevel,0,5],["Window (ticks)",window_,setWindow_,20,100]].map(([lbl,val,set,mn,mx])=>(
                <div key={lbl} style={{ marginBottom:12 }}>
                  <div style={{ display:"flex",justifyContent:"space-between",fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:".07em",marginBottom:4 }}>
                    <span>{lbl}</span><span style={{ color:T.accent }}>{val}</span>
                  </div>
                  <input type="range" min={mn} max={mx} value={val} onChange={e=>set(+e.target.value)}/>
                </div>
              ))}

              <div style={{ height:1,background:T.border,margin:"10px 0" }}/>
              <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".1em",textTransform:"uppercase",color:T.accent,marginBottom:8 }}>Alert Thresholds (kg)</div>
              {[["🔴 Critical",co2Critical,setCo2Critical,10,80],[" 🟠 High",co2High,setCo2High,5,60],["🟡 Medium",co2Medium,setCo2Medium,2,40]].map(([lbl,val,set,mn,mx])=>(
                <div key={lbl} style={{ marginBottom:10 }}>
                  <div style={{ display:"flex",justifyContent:"space-between",fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:T.muted,marginBottom:3 }}>
                    <span>{lbl}</span><span style={{ color:T.accent }}>{val}</span>
                  </div>
                  <input type="range" min={mn} max={mx} value={val} onChange={e=>set(+e.target.value)}/>
                </div>
              ))}

              <div style={{ height:1,background:T.border,margin:"10px 0" }}/>
              <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".1em",textTransform:"uppercase",color:T.accent,marginBottom:8 }}>Display Options</div>
              {[["Forecast Band",showForecast,setShowForecast],["Anomaly Markers",showAnomalies,setShowAnomalies],["Threshold Bands",showThresholds,setShowThresholds]].map(([lbl,val,set])=>(
                <label key={lbl} style={{ display:"flex",alignItems:"center",gap:8,cursor:"pointer",marginBottom:8,fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted }}>
                  <input type="checkbox" checked={val} onChange={e=>set(e.target.checked)} style={{ accentColor:T.accent }}/>
                  {lbl}
                </label>
              ))}

              <div style={{ height:1,background:T.border,margin:"10px 0" }}/>
              <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".1em",textTransform:"uppercase",color:T.accent,marginBottom:6 }}>AI Engine</div>
              <input type="password" placeholder="sk-ant-..." value={apiKey} onChange={e=>setApiKey(e.target.value)}
                style={{ width:"100%",background:dark?"#1a2236":"#eef0f7",border:`1px solid ${T.border}`,borderRadius:8,padding:"7px 10px",color:T.text,fontFamily:"'JetBrains Mono',monospace",fontSize:12 }}/>
            </div>

            {/* Status badge */}
            <div style={{
              background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",
              border:`1px solid ${status.color}`,borderRadius:14,padding:"14px 16px",
              fontFamily:"'JetBrains Mono',monospace",
            }} className={avg5co2>co2Critical?"glow-critical":""}>
              <div style={{ display:"flex",alignItems:"center",gap:8 }}>
                <span className="pulse-dot" style={{ background:status.color }}/>
                <div>
                  <div style={{ fontSize:10,color:T.muted,textTransform:"uppercase",letterSpacing:".1em" }}>System Status</div>
                  <div style={{ fontSize:15,fontWeight:700,color:status.color }}>{status.label}</div>
                  <div style={{ fontSize:10,color:T.muted,marginTop:2 }}>5-tick avg: {avg5co2.toFixed(1)} kg</div>
                </div>
              </div>
            </div>

            {/* Export buttons */}
            <div style={{ display:"flex",flexDirection:"column",gap:8 }}>
              <button style={{ ...btn("primary"),display:"flex",alignItems:"center",gap:8,justifyContent:"center" }} onClick={exportCSV}>
                <div style={{ width:14,height:14 }}><Icons.Download/></div>Export CSV
              </button>
              <button style={{ ...btn(),display:"flex",alignItems:"center",gap:8,justifyContent:"center",borderColor:alertLog.length?T.orange:T.border }} onClick={exportAlertCSV}>
                <div style={{ width:14,height:14 }}><Icons.AlertTriangle/></div>Export Alerts
              </button>
            </div>
          </div>

          {/* ── MAIN CONTENT ── */}
          <div style={{ display:"flex",flexDirection:"column",gap:16 }}>

            {/* Tab bar */}
            <div style={{ background:dark?"#1a2236":"#eef0f7",border:`1px solid ${T.border}`,borderRadius:12,padding:5,display:"flex",gap:4,flexWrap:"wrap" }}>
              {[["realtime","⚡ Real-Time"],["analytics","📊 Analytics"],["advanced","📈 Advanced"],["insights","🧠 AI Insights"],["compare","🤖 Compare"],["alerts","🚨 Alert Log"],["score","🎯 Score"]].map(([id,lbl])=>(
                <button key={id} style={tabStyle(id)} onClick={()=>setActiveTab(id)}>{lbl}</button>
              ))}
            </div>

            {/* ════ TAB: REAL-TIME ════ */}
            {activeTab==="realtime" && (
              <div className="fade-in">
                {sectionHead("⚡ Live System Monitoring")}

                {/* KPI ticker */}
                <div style={{ display:"flex",background:dark?"#111827":"#fff",border:`1px solid ${T.border}`,borderRadius:10,overflow:"hidden",marginBottom:14 }}>
                  {[["CO₂ kg",latest.co2.toFixed(1),T.red],[`${latest.queries}`,latest.queries,"Queries",T.accent],["kWh",latest.power.toFixed(0),T.green],[`${eff}`,"/100","Eff",T.purple],[status.label.split(" ").slice(1).join(" "),"","Status",status.color],["Alerts",totalAlerts,"",T.orange]].map(([val,sub,lbl,col],i,arr)=>(
                    <div key={i} style={{ flex:1,padding:"10px 14px",borderRight:i<arr.length-1?`1px solid ${T.border}`:"none",textAlign:"center",fontFamily:"'JetBrains Mono',monospace" }}>
                      <div style={{ fontSize:"1.1rem",fontWeight:700,color:typeof col==="string"&&col.startsWith("#")?col:T.text }}>{typeof val==="number"?val:val}</div>
                      <div style={{ fontSize:9,letterSpacing:".1em",textTransform:"uppercase",color:T.muted,marginTop:2 }}>{typeof lbl==="string"&&lbl||typeof sub==="string"&&sub||""}</div>
                    </div>
                  ))}
                </div>

                {/* Live chart */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16,marginBottom:14 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:12,color:T.muted,marginBottom:10 }}>
                    Live Monitor · {status.label} · {model}
                  </div>
                  <ResponsiveContainer width="100%" height={380}>
                    <AreaChart data={[...data,...forecastData.map(f=>({...f,co2:undefined}))]} margin={{top:10,right:30,bottom:0,left:0}}>
                      <defs>
                        <linearGradient id="gCo2" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor={T.red}    stopOpacity={0.25}/>
                          <stop offset="95%" stopColor={T.red}    stopOpacity={0.02}/>
                        </linearGradient>
                        <linearGradient id="gPow" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%"  stopColor={T.green}  stopOpacity={0.18}/>
                          <stop offset="95%" stopColor={T.green}  stopOpacity={0.02}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={T.border} strokeWidth={.5}/>
                      <XAxis dataKey="tick" stroke={T.border} tick={{fill:T.muted,fontFamily:"'JetBrains Mono',monospace",fontSize:10}}/>
                      <YAxis stroke={T.border} tick={{fill:T.muted,fontFamily:"'JetBrains Mono',monospace",fontSize:10}}/>
                      <Tooltip content={<CustomTooltip dark={dark}/>}/>
                      <Legend wrapperStyle={{fontFamily:"'JetBrains Mono',monospace",fontSize:11,paddingTop:8}}/>
                      {showThresholds && <>
                        <ReferenceLine y={co2Critical} stroke={T.red}    strokeDasharray="4 4" strokeWidth={1} label={{ value:`Crit ${co2Critical}`,fill:T.red,fontSize:10,fontFamily:"'JetBrains Mono',monospace" }}/>
                        <ReferenceLine y={co2High}     stroke={T.orange} strokeDasharray="4 4" strokeWidth={1} label={{ value:`High ${co2High}`,   fill:T.orange,fontSize:10,fontFamily:"'JetBrains Mono',monospace" }}/>
                        <ReferenceLine y={co2Medium}   stroke={T.yellow} strokeDasharray="4 4" strokeWidth={1} label={{ value:`Med ${co2Medium}`,  fill:T.yellow,fontSize:10,fontFamily:"'JetBrains Mono',monospace" }}/>
                      </>}
                      <Area type="monotone" dataKey="co2" name="CO₂ kg" stroke={T.red} fill="url(#gCo2)" strokeWidth={2.5} dot={false} activeDot={{r:5,fill:T.red}}/>
                      <Area type="monotone" dataKey="power" name="Power kWh" stroke={T.green} fill="url(#gPow)" strokeWidth={1.8} dot={false}/>
                      <Line type="monotone" dataKey="queries" name="Queries" stroke={T.accent} strokeWidth={1.8} dot={false}/>
                      {showForecast && <Line type="monotone" dataKey="co2Forecast" name="Forecast" stroke={T.orange} strokeDasharray="5 5" strokeWidth={2} dot={false}/>}
                      {showAnomalies && anomalies.map((a,i)=>(
                        <ReferenceLine key={i} x={a.tick} stroke={T.red} strokeWidth={1.5} label={{ value:"⚠", fill:T.red, fontSize:12 }}/>
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Data table */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,overflow:"hidden" }}>
                  <table style={{ width:"100%",borderCollapse:"collapse",fontFamily:"'JetBrains Mono',monospace",fontSize:12 }}>
                    <thead>
                      <tr style={{ background:dark?"#1a2236":"#eef0f7" }}>
                        {["Tick","Queries","CO₂ (kg)","Power (kWh)","Status"].map(h=>(
                          <th key={h} style={{ padding:"10px 14px",textAlign:"left",color:T.muted,fontSize:10,letterSpacing:".08em",textTransform:"uppercase",fontWeight:600,borderBottom:`1px solid ${T.border}` }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {data.slice(-10).reverse().map((row,i)=>{
                        const s=getStatus(row.co2,co2Critical,co2High,co2Medium);
                        return (
                          <tr key={i} style={{ borderBottom:`1px solid ${T.border}`,transition:"background .15s" }}
                            onMouseEnter={e=>e.currentTarget.style.background=dark?"rgba(56,189,248,.04)":"rgba(56,189,248,.06)"}
                            onMouseLeave={e=>e.currentTarget.style.background=""}>
                            <td style={{ padding:"9px 14px",color:T.muted }}>#{row.tick}</td>
                            <td style={{ padding:"9px 14px",color:T.accent }}>{row.queries}</td>
                            <td style={{ padding:"9px 14px",color:row.co2>co2High?T.red:row.co2>co2Medium?T.orange:T.text,fontWeight:row.co2>co2High?700:400 }}>{row.co2}</td>
                            <td style={{ padding:"9px 14px",color:T.green }}>{row.power}</td>
                            <td style={{ padding:"9px 14px" }}><span style={{ color:s.color,fontWeight:700,fontSize:11 }}>{s.label}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {aiSummary && <div style={{ background:"rgba(56,189,248,.07)",border:"1px solid rgba(56,189,248,.2)",borderRadius:10,padding:"12px 16px",fontFamily:"'Space Grotesk',sans-serif",fontSize:13.5,marginTop:8 }}>🤖 <strong>Auto Summary:</strong> {aiSummary}</div>}
              </div>
            )}

            {/* ════ TAB: ANALYTICS ════ */}
            {activeTab==="analytics" && (
              <div className="fade-in">
                {sectionHead("📊 System Analytics")}
                <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10,marginBottom:16 }}>
                  <MetricCard label="Avg CO₂"   value={avgCo2.toFixed(2)} icon={Icons.Cloud}      iconColor={T.red}   dark={dark} accent={T.red}/>
                  <MetricCard label="Peak CO₂"  value={peakCo2.toFixed(2)} icon={Icons.TrendingUp} iconColor={T.orange} dark={dark} accent={T.orange}/>
                  <MetricCard label="Avg Power" value={(data.reduce((s,d)=>s+d.power,0)/Math.max(data.length,1)).toFixed(2)} icon={Icons.Zap} iconColor={T.yellow} dark={dark} accent={T.yellow}/>
                  <MetricCard label="Efficiency" value={`${eff}/100`} icon={Icons.Activity} iconColor={T.green} dark={dark} accent={T.green}/>
                </div>

                {/* Smoothed trends */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16,marginBottom:14 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📈 Smoothed Trends (5-tick rolling avg)</div>
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={data}>
                      <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                      <XAxis dataKey="tick" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <Tooltip content={<CustomTooltip dark={dark}/>}/>
                      <Legend wrapperStyle={{fontFamily:"'JetBrains Mono',monospace",fontSize:11}}/>
                      <Line type="monotone" dataKey="co2"     name="CO₂"    stroke={T.red}    strokeWidth={2} dot={false}/>
                      <Line type="monotone" dataKey="queries" name="Queries" stroke={T.accent} strokeWidth={1.8} dot={false}/>
                      <Line type="monotone" dataKey="power"   name="Power"  stroke={T.green}  strokeWidth={1.8} dot={false}/>
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:14 }}>
                  {/* Forecast */}
                  <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                    <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>🔮 CO₂ Forecast · Holt's Smoothing</div>
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={[...data.slice(-20).map((d,i)=>({...d,isForecast:false})),...forecastData.map(f=>({tick:f.tick,co2Forecast:f.co2Forecast,upper:f.upper,lower:f.lower,isForecast:true}))]}>
                        <defs>
                          <linearGradient id="gFc" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%"  stopColor={T.orange} stopOpacity={.2}/>
                            <stop offset="100%" stopColor={T.orange} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                        <XAxis dataKey="tick" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <Tooltip content={<CustomTooltip dark={dark}/>}/>
                        <ReferenceLine y={co2Critical} stroke={T.red} strokeDasharray="4 4" strokeWidth={1}/>
                        <Area type="monotone" dataKey="co2"         name="CO₂"     stroke={T.red}    fill="none"        strokeWidth={2} dot={false}/>
                        <Area type="monotone" dataKey="co2Forecast" name="Forecast" stroke={T.orange} fill="url(#gFc)"  strokeWidth={2} strokeDasharray="5 5" dot={false}/>
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Correlation heatmap proxy (scatter) */}
                  <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                    <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>🔗 Load vs Emissions Scatter</div>
                    <ResponsiveContainer width="100%" height={250}>
                      <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                        <XAxis dataKey="queries" name="Queries" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <YAxis dataKey="co2"     name="CO₂ kg"  tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <Tooltip content={<CustomTooltip dark={dark}/>}/>
                        <Scatter name="Query vs CO₂" data={data} fill={T.accent}>
                          {data.map((d,i)=><Cell key={i} fill={d.co2>co2Critical?T.red:d.co2>co2High?T.orange:d.co2>co2Medium?T.yellow:T.green}/>)}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            )}

            {/* ════ TAB: ADVANCED ════ */}
            {activeTab==="advanced" && (
              <div className="fade-in">
                {sectionHead("📈 Advanced Insights")}
                {data.length < 8 ? (
                  <div style={{ background:"rgba(251,191,36,.08)",border:"1px solid rgba(251,191,36,.3)",borderRadius:10,padding:16,color:T.yellow,fontFamily:"'JetBrains Mono',monospace",fontSize:13 }}>⚠️ Start the simulation — need more data for advanced views.</div>
                ) : (
                  <>
                    <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14 }}>
                      {/* Gauge proxy — CO2 stress bar */}
                      <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:20 }}>
                        <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:14,textTransform:"uppercase",letterSpacing:".08em" }}>⚡ CO₂ Stress Gauge</div>
                        <div style={{ textAlign:"center",marginBottom:16 }}>
                          <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"3rem",fontWeight:700,color:status.color,lineHeight:1 }}>{latest.co2.toFixed(1)}</div>
                          <div style={{ fontSize:12,color:T.muted,marginTop:4 }}>kg CO₂ / tick</div>
                        </div>
                        {[["Low",0,co2Medium,T.green],[`Med`,co2Medium,co2High,T.yellow],["High",co2High,co2Critical,T.orange],["Crit",co2Critical,co2Critical*1.4,T.red]].map(([lbl,lo,hi,col])=>{
                          const pct = Math.min(100,Math.max(0,(latest.co2-lo)/(hi-lo)*100));
                          const active = latest.co2 >= lo && latest.co2 < hi;
                          return (
                            <div key={lbl} style={{ marginBottom:8 }}>
                              <div style={{ display:"flex",justifyContent:"space-between",fontFamily:"'JetBrains Mono',monospace",fontSize:10,color:active?col:T.muted,marginBottom:3 }}>
                                <span style={{ fontWeight:active?700:400 }}>{lbl}</span><span>{lo.toFixed(0)}–{hi.toFixed(0)} kg</span>
                              </div>
                              <div style={{ background:dark?"#1a2236":"#eef0f7",borderRadius:5,height:6,overflow:"hidden" }}>
                                <div style={{ height:"100%",borderRadius:5,background:col,width:active?`${pct}%`:latest.co2>=hi?"100%":"0%",opacity:active?1:.3,transition:"width .5s ease" }}/>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Anomaly bar */}
                      <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:20 }}>
                        <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>🚨 Anomaly Detection</div>
                        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14 }}>
                          <MetricCard label="Detected" value={anomalies.length} dark={dark} accent={anomalies.length?T.red:T.green}/>
                          <MetricCard label="Rate" value={`${(anomalies.length/Math.max(data.length,1)*100).toFixed(1)}%`} dark={dark} accent={T.orange}/>
                        </div>
                        <ResponsiveContainer width="100%" height={180}>
                          <BarChart data={data.slice(-20)}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                            <XAxis dataKey="tick" tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <YAxis tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <Tooltip content={<CustomTooltip dark={dark}/>}/>
                            <Bar dataKey="co2" name="CO₂">
                              {data.slice(-20).map((d,i)=>{
                                const isAnom = anomalies.some(a=>a.tick===d.tick);
                                return <Cell key={i} fill={isAnom?T.red:d.co2>co2High?T.orange:d.co2>co2Medium?T.yellow:T.green}/>;
                              })}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Per-query efficiency */}
                    <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>🔋 Per-Query Efficiency Over Time</div>
                      <ResponsiveContainer width="100%" height={240}>
                        <LineChart data={data.map(d=>({ ...d, co2pq: +(d.co2/Math.max(d.queries,1)).toFixed(3), powpq: +(d.power/Math.max(d.queries,1)).toFixed(3) }))}>
                          <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                          <XAxis dataKey="tick" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                          <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                          <Tooltip content={<CustomTooltip dark={dark}/>}/>
                          <Legend wrapperStyle={{fontFamily:"'JetBrains Mono',monospace",fontSize:11}}/>
                          <Line type="monotone" dataKey="co2pq"  name="CO₂/Query"   stroke={T.red}    strokeWidth={2} dot={false}/>
                          <Line type="monotone" dataKey="powpq"  name="Power/Query" stroke={T.purple} strokeWidth={2} dot={false}/>
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ════ TAB: AI INSIGHTS ════ */}
            {activeTab==="insights" && (
              <div className="fade-in">
                {sectionHead("🧠 AI Decision Engine")}
                {/* Risk banner */}
                {latest.co2>co2Critical ? (
                  <div style={{ background:"rgba(248,113,113,.1)",border:"1px solid rgba(248,113,113,.4)",borderRadius:10,padding:"12px 16px",color:T.red,fontFamily:"'Space Grotesk',sans-serif",fontSize:14,marginBottom:10 }}>
                    🚨 <strong>Critical System State</strong> — Immediate action required
                  </div>
                ) : latest.co2>co2Medium ? (
                  <div style={{ background:"rgba(251,191,36,.08)",border:"1px solid rgba(251,191,36,.35)",borderRadius:10,padding:"12px 16px",color:T.yellow,fontFamily:"'Space Grotesk',sans-serif",fontSize:14,marginBottom:10 }}>
                    ⚠️ <strong>Moderate Risk</strong> — Monitor and optimize
                  </div>
                ) : (
                  <div style={{ background:"rgba(52,211,153,.08)",border:"1px solid rgba(52,211,153,.35)",borderRadius:10,padding:"12px 16px",color:T.green,fontFamily:"'Space Grotesk',sans-serif",fontSize:14,marginBottom:10 }}>
                    ✅ <strong>Healthy System</strong> — Within acceptable thresholds
                  </div>
                )}

                <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:14 }}>
                  <MetricCard label="🔮 Next CO₂ (forecast)" value={`${linearForecast(data.map(d=>d.co2),1)[0]} kg`} delta={+(linearForecast(data.map(d=>d.co2),1)[0]-latest.co2).toFixed(1)} dark={dark} accent={T.orange}/>
                  <MetricCard label="📊 Risk Level" value={latest.co2>co2Critical?"HIGH":latest.co2>co2Medium?"MEDIUM":"LOW"} dark={dark} accent={latest.co2>co2Critical?T.red:latest.co2>co2Medium?T.yellow:T.green}/>
                </div>

                {/* Recommendations */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:18,marginBottom:14 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:12,textTransform:"uppercase",letterSpacing:".08em" }}>🤖 Recommendations</div>
                  {(latest.co2>co2Critical?[
                    "Shift workloads to off-peak hours — lower-carbon grid windows",
                    "Enable model compression / quantization to cut per-query footprint",
                    `Switch to Sonar (${MODEL_SPECS["Sonar"].co2} factor) — ${Math.round((1-MODEL_SPECS["Sonar"].co2/MODEL_SPECS[model].co2)*100)}% CO₂ reduction`,
                    "Reduce concurrent load immediately — enable request queuing",
                  ]:latest.co2>co2Medium?[
                    "Optimise request batching to lower per-query overhead",
                    "Eliminate redundant model calls via smarter routing",
                    "Schedule heavy jobs during renewable-heavy grid windows",
                  ]:[
                    "Maintain current config — system is healthy",
                    "Monitor for drift in query patterns",
                    "Explore prompt compression for further gains",
                  ]).map((r,i)=>(
                    <div key={i} style={{ display:"flex",gap:10,marginBottom:8,fontFamily:"'Space Grotesk',sans-serif",fontSize:13.5 }}>
                      <span style={{ color:T.accent,fontFamily:"'JetBrains Mono',monospace",fontWeight:700,flexShrink:0 }}>{i+1}.</span>
                      <span style={{ color:T.text }}>{r}</span>
                    </div>
                  ))}
                </div>

                {/* Model benchmark bar */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16,marginBottom:14 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📐 Model CO₂ Benchmark</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={Object.entries(MODEL_SPECS).map(([n,s])=>({ name:n.split(" ")[0], co2:s.co2, isCurrent:n===model }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                      <XAxis dataKey="name" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <Tooltip content={<CustomTooltip dark={dark}/>}/>
                      <ReferenceLine y={avgCo2/Math.max(data.reduce((s,d)=>s+d.queries,0)/Math.max(data.length,1),1)} stroke={T.purple} strokeDasharray="5 5"/>
                      <Bar dataKey="co2" name="CO₂ Factor">
                        {Object.entries(MODEL_SPECS).map(([n],i)=><Cell key={i} fill={n===model?T.accent:T.muted} opacity={n===model?1:.5}/>)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Chat */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:18 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:12,textTransform:"uppercase",letterSpacing:".08em" }}>💬 Ask the AI Sustainability Expert</div>
                  <div style={{ maxHeight:320,overflowY:"auto",marginBottom:12,display:"flex",flexDirection:"column",gap:8 }}>
                    {chatHistory.map((m,i)=>(
                      <div key={i} style={{
                        background:m.role==="user"?dark?"linear-gradient(135deg,#1a2236,#111827)":"linear-gradient(135deg,#eef0f7,#fff)":"linear-gradient(135deg,rgba(56,189,248,.07),rgba(56,189,248,.03))",
                        border:`1px solid ${m.role==="user"?T.border:"rgba(56,189,248,.22)"}`,
                        borderRadius:m.role==="user"?"14px 14px 4px 14px":"14px 14px 14px 4px",
                        padding:"11px 15px",fontSize:13.5,
                      }}>
                        <strong style={{ color:m.role==="user"?T.accent:T.green,fontSize:12,fontFamily:"'JetBrains Mono',monospace" }}>{m.role==="user"?"You":"🤖 AI"}</strong>
                        <div style={{ marginTop:5,color:T.text }}>{m.content}</div>
                      </div>
                    ))}
                    {aiLoading && <div style={{ color:T.muted,fontFamily:"'JetBrains Mono',monospace",fontSize:12 }}>Analyzing…</div>}
                  </div>
                  <div style={{ display:"flex",gap:8 }}>
                    <textarea value={chatInput} onChange={e=>setChatInput(e.target.value)} onKeyDown={e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();sendChat();}}}
                      placeholder="e.g. How can I cut CO₂ at peak load?" rows={2}
                      style={{ flex:1,background:dark?"#1a2236":"#eef0f7",border:`1px solid ${T.border}`,borderRadius:8,padding:"9px 12px",color:T.text,fontFamily:"'JetBrains Mono',monospace",fontSize:13,resize:"none" }}/>
                    <div style={{ display:"flex",flexDirection:"column",gap:6 }}>
                      <button style={{ ...btn("primary"),padding:"9px 16px" }} onClick={sendChat} disabled={!apiKey||aiLoading}>🚀</button>
                      <button style={{ ...btn("danger"),padding:"9px 16px" }} onClick={()=>setChatHistory([])}>🗑</button>
                    </div>
                  </div>
                  {!apiKey && <div style={{ color:T.muted,fontFamily:"'JetBrains Mono',monospace",fontSize:11,marginTop:6 }}>⚠️ Add your API key in the sidebar to enable AI chat.</div>}
                </div>
              </div>
            )}

            {/* ════ TAB: MODEL COMPARE ════ */}
            {activeTab==="compare" && (
              <div className="fade-in">
                {sectionHead("🤖 Model Comparison")}
                <div style={{ fontSize:12,color:T.muted,fontFamily:"'JetBrains Mono',monospace",marginBottom:14 }}>Based on avg load: <strong style={{ color:T.accent }}>{Math.round(latest.queries)} queries/tick</strong></div>

                {/* Table */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,overflow:"hidden",marginBottom:14 }}>
                  <table style={{ width:"100%",borderCollapse:"collapse",fontFamily:"'JetBrains Mono',monospace",fontSize:12 }}>
                    <thead>
                      <tr style={{ background:dark?"#1a2236":"#eef0f7" }}>
                        {["Model","CO₂ (kg)","Power (kWh)","Efficiency (%)","Cost ($)"].map(h=>(
                          <th key={h} style={{ padding:"10px 14px",textAlign:"left",color:T.muted,fontSize:10,letterSpacing:".08em",textTransform:"uppercase",borderBottom:`1px solid ${T.border}` }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {compareRows.map((r,i)=>(
                        <tr key={i} style={{ borderBottom:`1px solid ${T.border}`,background:r.name===model?"rgba(56,189,248,.06)":"" }}>
                          <td style={{ padding:"10px 14px",fontWeight:r.name===model?700:400,color:r.name===model?T.accent:T.text }}>
                            <span style={{ width:8,height:8,borderRadius:"50%",background:MODEL_SPECS[r.name]?.color,display:"inline-block",marginRight:8 }}/>
                            {r.name}
                          </td>
                          <td style={{ padding:"10px 14px",color:T.red }}>{r.co2}</td>
                          <td style={{ padding:"10px 14px",color:T.green }}>{r.power}</td>
                          <td style={{ padding:"10px 14px",color:T.accent }}>{r.eff}%</td>
                          <td style={{ padding:"10px 14px",color:T.yellow }}>${r.cost}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginBottom:14 }}>
                  {/* CO2 bar */}
                  <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                    <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>CO₂ by Model</div>
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={compareRows} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                        <XAxis type="number" tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <YAxis type="category" dataKey="name" tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border} width={80}/>
                        <Tooltip content={<CustomTooltip dark={dark}/>}/>
                        <Bar dataKey="co2" name="CO₂ kg">
                          {compareRows.map((r,i)=><Cell key={i} fill={r.name===model?T.accent:MODEL_SPECS[r.name]?.color||T.muted}/>)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Radar */}
                  <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                    <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>🕸️ Multi-Dimensional Radar</div>
                    <ResponsiveContainer width="100%" height={260}>
                      <RadarChart data={[
                        {dim:"Efficiency"}, {dim:"Low CO₂"}, {dim:"Low Power"}, {dim:"Cost"}, {dim:"Stability"}
                      ]}>
                        <PolarGrid stroke={T.border}/>
                        <PolarAngleAxis dataKey="dim" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}}/>
                        <PolarRadiusAxis domain={[0,100]} tick={{fill:T.muted,fontSize:8}} stroke={T.border}/>
                        {Object.entries(MODEL_SPECS).map(([n,s])=>{
                          const d=[{dim:"Efficiency",v:s.efficiency*100},{dim:"Low CO₂",v:(1-s.co2/0.62)*100},{dim:"Low Power",v:(1-s.power/3.1)*100},{dim:"Cost",v:(1-s.co2/0.62)*100},{dim:"Stability",v:(s.efficiency*100+((1-s.co2/0.62)*100))/2}];
                          return <Radar key={n} name={n} dataKey="v" data={d} stroke={s.color} fill={s.color} fillOpacity={n===model?.18:.06} strokeWidth={n===model?2.5:1}/>;
                        })}
                        <Legend wrapperStyle={{fontFamily:"'JetBrains Mono',monospace",fontSize:10}}/>
                        <Tooltip content={<CustomTooltip dark={dark}/>}/>
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                <div style={{ background:"rgba(52,211,153,.07)",border:"1px solid rgba(52,211,153,.3)",borderRadius:10,padding:"12px 16px",color:T.green,fontFamily:"'Space Grotesk',sans-serif",fontSize:14 }}>
                  ✅ Most efficient: <strong>{compareRows[0]?.name}</strong>
                  {model===compareRows[compareRows.length-1]?.name && <span style={{ color:T.yellow,marginLeft:12 }}>⚠️ You're on the highest-CO₂ model — consider switching for {Math.round((1-MODEL_SPECS[compareRows[0]?.name]?.co2/MODEL_SPECS[model]?.co2)*100)}% reduction.</span>}
                </div>
              </div>
            )}

            {/* ════ TAB: ALERT LOG ════ */}
            {activeTab==="alerts" && (
              <div className="fade-in">
                {sectionHead("🚨 Alert History & Event Log")}
                <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10,marginBottom:16 }}>
                  <MetricCard label="Total Events" value={alertLog.length}  dark={dark}/>
                  <MetricCard label="🔴 Critical"  value={alertLog.filter(a=>a.level==="CRITICAL").length} dark={dark} accent={T.red}/>
                  <MetricCard label="🟠 High"       value={alertLog.filter(a=>a.level==="HIGH").length}     dark={dark} accent={T.orange}/>
                  <MetricCard label="🟡 Medium"     value={alertLog.filter(a=>a.level==="MEDIUM").length}   dark={dark} accent={T.yellow}/>
                </div>

                <div style={{ display:"flex",gap:10,marginBottom:14,flexWrap:"wrap" }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,padding:"8px 14px",background:dark?"#1a2236":"#eef0f7",borderRadius:8,border:`1px solid ${T.border}`,flex:1 }}>
                    Showing {alertLog.length} events · Lower thresholds → more alerts
                  </div>
                  <button style={{ ...btn("danger"),whiteSpace:"nowrap" }} onClick={()=>{ setAlertLog([]); setTotalAlerts(0); }}>🗑️ Clear Log</button>
                  <button style={{ ...btn(),whiteSpace:"nowrap",borderColor:alertLog.length?T.orange:T.border }} onClick={exportAlertCSV}>📁 Export CSV</button>
                </div>

                {/* Alert list */}
                <div style={{ display:"flex",flexDirection:"column",gap:4,maxHeight:480,overflowY:"auto" }}>
                  {alertLog.length===0 ? (
                    <div style={{ background:"rgba(56,189,248,.06)",border:"1px solid rgba(56,189,248,.2)",borderRadius:10,padding:20,textAlign:"center",fontFamily:"'JetBrains Mono',monospace",fontSize:13,color:T.muted }}>
                      No events yet. Start the simulation — alerts fire when CO₂ crosses thresholds<br/>
                      <span style={{ color:T.accent }}>Medium: {co2Medium} kg · High: {co2High} kg · Critical: {co2Critical} kg</span>
                    </div>
                  ) : alertLog.slice(0,60).map((e,i)=><AlertEntry key={i} entry={e} dark={dark}/>)}
                </div>

                {/* Frequency chart */}
                {alertLog.length >= 3 && (() => {
                  const counts = alertLog.reduce((acc,a)=>{ acc[a.level]=(acc[a.level]||0)+1; return acc; },{});
                  const pieData = Object.entries(counts).map(([k,v])=>({ name:k, value:v }));
                  return (
                    <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginTop:14 }}>
                      <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                        <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📊 Alert Breakdown</div>
                        <ResponsiveContainer width="100%" height={220}>
                          <BarChart data={pieData}>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                            <XAxis dataKey="name" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <Tooltip content={<CustomTooltip dark={dark}/>}/>
                            <Bar dataKey="value" name="Count">
                              {pieData.map((e,i)=><Cell key={i} fill={e.name==="CRITICAL"?T.red:e.name==="HIGH"?T.orange:T.yellow}/>)}
                            </Bar>
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16 }}>
                        <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📈 Alert CO₂ Levels</div>
                        <ResponsiveContainer width="100%" height={220}>
                          <ScatterChart>
                            <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                            <XAxis dataKey="tick" name="Tick" tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <YAxis dataKey="co2"  name="CO₂"  tick={{fill:T.muted,fontSize:9,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                            <Tooltip content={<CustomTooltip dark={dark}/>}/>
                            <Scatter data={alertLog.slice(0,40).reverse()}>
                              {alertLog.slice(0,40).reverse().map((a,i)=><Cell key={i} fill={a.level==="CRITICAL"?T.red:a.level==="HIGH"?T.orange:T.yellow}/>)}
                            </Scatter>
                          </ScatterChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* ════ TAB: SCORE & PROJECTIONS ════ */}
            {activeTab==="score" && (
              <div className="fade-in">
                {sectionHead("🎯 Sustainability Scorecard & Projections")}

                {/* Scorecard */}
                <div style={{ display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:10,marginBottom:16 }}>
                  <ScoreCard label="Overall"     value={+overallScore} detail="Composite"     dark={dark}/>
                  <ScoreCard label="Efficiency"  value={+eff}          detail="CO₂/query"    dark={dark}/>
                  <ScoreCard label="Stability"   value={+stability}    detail="Variance ctrl" dark={dark}/>
                  <ScoreCard label="Carbon Int." value={+carbonInt}    detail="Intensity"    dark={dark}/>
                  <ScoreCard label="Alert Health"value={+alertScore}   detail="Alert burden" dark={dark}/>
                </div>

                {/* Grade */}
                <div style={{ textAlign:"center",padding:28,background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`2px solid ${gradeColor}`,borderRadius:18,marginBottom:16,boxShadow:`0 8px 32px rgba(0,0,0,.3)` }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:10,letterSpacing:".18em",textTransform:"uppercase",color:T.muted }}>Sustainability Grade</div>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"5rem",fontWeight:700,color:gradeColor,lineHeight:1.05 }}>{grade}</div>
                  <div style={{ fontSize:13,color:T.muted }}>{model} · Score: {overallScore}/100 · {new Date().toLocaleString()}</div>
                </div>

                {/* Score history */}
                {sessionSnapshots.length > 1 && (
                  <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16,marginBottom:16 }}>
                    <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📈 Session Performance History</div>
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={sessionSnapshots}>
                        <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                        <XAxis dataKey="tick" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <YAxis yAxisId="left"  tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <YAxis yAxisId="right" orientation="right" tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                        <Tooltip content={<CustomTooltip dark={dark}/>}/>
                        <Legend wrapperStyle={{fontFamily:"'JetBrains Mono',monospace",fontSize:11}}/>
                        <Line yAxisId="left"  type="monotone" dataKey="co2"     name="CO₂ kg" stroke={T.red}   strokeWidth={2.2} dot={{r:3,fill:T.red}}/>
                        <Line yAxisId="right" type="monotone" dataKey="queries" name="Queries" stroke={T.accent} strokeWidth={2.2} dot={{r:3,fill:T.accent}}/>
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Projections */}
                <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,textTransform:"uppercase",letterSpacing:".08em",marginBottom:10 }}>💰 Cost & Carbon Projections</div>
                <div style={{ display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10,marginBottom:14 }}>
                  {[["Daily",projDaily,+(projDaily*CARBON_PRICE).toFixed(2),T.green],["Weekly",projWeekly,+(projWeekly*CARBON_PRICE).toFixed(2),T.accent],["Monthly",projMonthly,+(projMonthly*CARBON_PRICE).toFixed(2),T.yellow],["Yearly",projYearly,+(projYearly*CARBON_PRICE).toFixed(2),T.red]].map(([lbl,co2,cost,col])=>(
                    <div key={lbl} style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:12,padding:"16px 18px",borderLeft:`4px solid ${col}`,transition:"all .22s ease" }}
                      onMouseEnter={e=>{e.currentTarget.style.transform="translateY(-2px)";e.currentTarget.style.boxShadow="0 8px 28px rgba(0,0,0,.25)";}}
                      onMouseLeave={e=>{e.currentTarget.style.transform="";e.currentTarget.style.boxShadow="";}}>
                      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:9.5,letterSpacing:".1em",textTransform:"uppercase",color:T.muted,marginBottom:6 }}>{lbl}</div>
                      <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:"1.5rem",fontWeight:700,color:col }}>${cost}</div>
                      <div style={{ fontSize:11.5,color:T.muted,marginTop:5 }}>📦 {co2} kg CO₂<br/>🌳 {treesNeeded(co2)} trees/yr</div>
                    </div>
                  ))}
                </div>

                {/* Projection bar */}
                <div style={{ background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:14,padding:16,marginBottom:14 }}>
                  <div style={{ fontFamily:"'JetBrains Mono',monospace",fontSize:11,color:T.muted,marginBottom:10,textTransform:"uppercase",letterSpacing:".08em" }}>📊 Projected CO₂ Accumulation</div>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={[["Session",+cumCo2.toFixed(1),T.green],["Daily",projDaily,T.accent],["Weekly",projWeekly,T.yellow],["Monthly",projMonthly,T.orange],["Yearly",projYearly,T.red]].map(([n,v,c])=>({name:n,co2:v,fill:c}))}>
                      <CartesianGrid strokeDasharray="3 3" stroke={T.border}/>
                      <XAxis dataKey="name" tick={{fill:T.muted,fontSize:11,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <YAxis tick={{fill:T.muted,fontSize:10,fontFamily:"'JetBrains Mono',monospace"}} stroke={T.border}/>
                      <Tooltip content={<CustomTooltip dark={dark}/>}/>
                      <Bar dataKey="co2" name="CO₂ kg">
                        {[T.green,T.accent,T.yellow,T.orange,T.red].map((c,i)=><Cell key={i} fill={c}/>)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Switch savings */}
                {(() => {
                  const best = Object.entries(MODEL_SPECS).sort((a,b)=>a[1].co2-b[1].co2)[0];
                  if (model===best[0]) return <div style={{ background:"rgba(52,211,153,.07)",border:"1px solid rgba(52,211,153,.3)",borderRadius:10,padding:"12px 16px",color:T.green,fontFamily:"'Space Grotesk',sans-serif",fontSize:14 }}>✅ Most efficient model: <strong>{model}</strong></div>;
                  const ratio = best[1].co2/MODEL_SPECS[model].co2;
                  const sv = +(projYearly*(1-ratio)).toFixed(1);
                  return (
                    <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:10 }}>
                      <div style={{ background:"rgba(52,211,153,.07)",border:"1px solid rgba(52,211,153,.3)",borderRadius:10,padding:"12px 16px",color:T.green,fontFamily:"'Space Grotesk',sans-serif",fontSize:14 }}>
                        💡 Switch to <strong>{best[0]}</strong> → save <strong>{sv} kg CO₂/yr</strong> ({Math.round((1-ratio)*100)}% reduction)
                      </div>
                      <div style={{ background:"rgba(56,189,248,.06)",border:"1px solid rgba(56,189,248,.25)",borderRadius:10,padding:"12px 16px",color:T.accent,fontFamily:"'Space Grotesk',sans-serif",fontSize:14 }}>
                        💰 Annual saving: <strong>${(sv*CARBON_PRICE).toFixed(2)}</strong> · 🌳 {treesNeeded(sv)} offset trees freed/yr
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}

          </div>{/* end main content */}
        </div>{/* end sidebar+main grid */}

        {/* ══════════ FOOTER ══════════ */}
        <div style={{ marginTop:20,background:dark?"linear-gradient(135deg,#111827,#1a2236)":"#fff",border:`1px solid ${T.border}`,borderRadius:12,padding:"12px 22px",display:"flex",justifyContent:"space-between",alignItems:"center",fontFamily:"'JetBrains Mono',monospace",fontSize:11.5,color:T.muted,flexWrap:"wrap",gap:8 }}>
          <span>⚡ AI Sustainability Dashboard v5</span>
          <span>Score: <strong style={{ color:gradeColor }}>{overallScore}/100</strong></span>
          <span>Uptime: {elapsed}</span>
          <span>Model: <strong style={{ color:MODEL_SPECS[model].color }}>{model}</strong></span>
          <span>Queries: <strong style={{ color:T.text }}>{totalQ.toLocaleString()}</strong></span>
          <span>Alerts: <strong style={{ color:totalAlerts>3?T.red:T.text }}>{totalAlerts}</strong></span>
        </div>

      </div>
    </div>
  );
}
