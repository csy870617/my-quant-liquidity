import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from zoneinfo import ZoneInfo

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 페이지 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="유동성 × 시장 분석기", 
    page_icon="icon.png",
    layout="wide"
)

try:
    st.logo("icon.png")
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 (PST 09:00/18:00 + KST 09:00/18:00 = 하루 4회)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_next_refresh():
    """다음 새로고침 시각까지 남은 초 계산 (PST 09/18 + KST 09/18)"""
    utc_now = datetime.now(ZoneInfo("UTC"))
    utc_hours = [0, 2, 9, 17]

    targets = []
    for h in utc_hours:
        t = utc_now.replace(hour=h, minute=0, second=0, microsecond=0)
        if t <= utc_now:
            t += timedelta(days=1)
        targets.append(t)

    next_t = min(targets)
    secs = max(int((next_t - utc_now).total_seconds()), 60)
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()

auto_interval = min(REFRESH_SECS * 1000, 3600_000)
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 MODERN DARK UI DESIGN - Naver Stock Style + Hip & Modern
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    /* 🌙 Dark Mode Colors */
    --bg-primary: #0a0e27;
    --bg-secondary: #111534;
    --bg-tertiary: #1a1f42;
    --surface: rgba(255, 255, 255, 0.04);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.1);
    --border-strong: rgba(255, 255, 255, 0.2);
    
    --text-primary: #ffffff;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    
    /* 💫 Neon Accents */
    --neon-blue: #60a5fa;
    --neon-cyan: #22d3ee;
    --neon-green: #34d399;
    --neon-red: #f87171;
    --neon-purple: #a78bfa;
    --neon-amber: #fbbf24;
    --neon-pink: #f472b6;
    
    /* 🎨 Gradients */
    --gradient-main: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --gradient-blue: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
    --gradient-green: linear-gradient(135deg, #34d399 0%, #10b981 100%);
    --gradient-red: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
    --gradient-purple: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
    
    /* ✨ Shadows & Glows */
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.5);
    --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.6);
    --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.7);
    --glow-blue: 0 0 30px rgba(96, 165, 250, 0.4);
    --glow-green: 0 0 30px rgba(52, 211, 153, 0.4);
    --glow-red: 0 0 30px rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 🌐 GLOBAL STYLES */
/* ══════════════════════════════════════════ */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    padding: 2.5rem 3rem 3rem 3rem !important;
    max-width: 1600px !important;
}

/* ══════════════════════════════════════════ */
/* 📋 HEADER - Ultra Modern */
/* ══════════════════════════════════════════ */
.page-header {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 0.8rem;
    padding: 2rem 2.5rem;
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 24px;
    box-shadow: var(--shadow-md), var(--glow-blue);
}

.page-header-icon {
    width: 60px;
    height: 60px;
    background: var(--gradient-main);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: var(--shadow-lg);
    animation: float 4s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-8px) rotate(2deg); }
}

.page-title {
    font-size: 2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #ffffff 0%, var(--neon-cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    text-shadow: 0 0 40px rgba(34, 211, 238, 0.3);
}

.page-desc {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-bottom: 2rem;
    line-height: 1.8;
}

/* ══════════════════════════════════════════ */
/* 🎴 CARDS - Glassmorphism */
/* ══════════════════════════════════════════ */
.card {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    background: var(--surface-hover);
    border-color: var(--border-strong);
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}

.card-title {
    font-size: 0.8rem;
    font-weight: 800;
    color: var(--neon-cyan);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.card-title .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 2s infinite;
    box-shadow: 0 0 15px currentColor;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.3); }
}

/* ══════════════════════════════════════════ */
/* 📊 KPI CARDS - Neon Glow */
/* ══════════════════════════════════════════ */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.kpi {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 22px;
    padding: 1.8rem 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 5px;
    border-radius: 22px 0 0 22px;
}

.kpi::after {
    content: '';
    position: absolute;
    top: -100%;
    right: -100%;
    width: 300%;
    height: 300%;
    opacity: 0;
    transition: opacity 0.4s;
}

.kpi:hover {
    transform: translateY(-6px);
    box-shadow: var(--shadow-lg);
    border-color: var(--border-strong);
}

.kpi:hover::after {
    opacity: 0.05;
}

.kpi.blue::before { background: var(--gradient-blue); }
.kpi.blue::after { background: radial-gradient(circle, var(--neon-blue) 0%, transparent 70%); }
.kpi.blue:hover { box-shadow: var(--shadow-lg), var(--glow-blue); }

.kpi.red::before { background: var(--gradient-red); }
.kpi.red::after { background: radial-gradient(circle, var(--neon-red) 0%, transparent 70%); }
.kpi.red:hover { box-shadow: var(--shadow-lg), var(--glow-red); }

.kpi.green::before { background: var(--gradient-green); }
.kpi.green::after { background: radial-gradient(circle, var(--neon-green) 0%, transparent 70%); }
.kpi.green:hover { box-shadow: var(--shadow-lg), var(--glow-green); }

.kpi.purple::before { background: var(--gradient-purple); }
.kpi.purple::after { background: radial-gradient(circle, var(--neon-purple) 0%, transparent 70%); }

.kpi-label {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 0.7rem;
}

.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1.2;
    text-shadow: 0 2px 10px rgba(255, 255, 255, 0.15);
}

.kpi-delta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    margin-top: 0.5rem;
}

.kpi-delta.up {
    color: var(--neon-green);
    text-shadow: 0 0 15px rgba(52, 211, 153, 0.4);
}

.kpi-delta.down {
    color: var(--neon-red);
    text-shadow: 0 0 15px rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 📢 REPORT BOX - Premium Gradient */
/* ══════════════════════════════════════════ */
.report-box {
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
    backdrop-filter: blur(40px);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    box-shadow: var(--shadow-md), 0 0 50px rgba(96, 165, 250, 0.15);
}

.report-header {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 1.2rem;
}

.report-badge {
    background: var(--gradient-blue);
    color: white;
    font-size: 0.7rem;
    font-weight: 900;
    padding: 6px 16px;
    border-radius: 24px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    box-shadow: 0 4px 15px rgba(96, 165, 250, 0.4);
}

.report-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
}

.report-title {
    font-size: 1.3rem;
    font-weight: 900;
    color: var(--text-primary);
    margin-bottom: 1rem;
    line-height: 1.5;
}

.report-body {
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 2;
}

.report-body strong {
    color: var(--text-primary);
    font-weight: 800;
}

.report-body .hl {
    background: rgba(96, 165, 250, 0.2);
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 800;
    color: var(--neon-cyan);
}

.report-divider {
    border: none;
    border-top: 1px dashed var(--border-strong);
    margin: 1.5rem 0;
}

.report-signal {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 18px;
    border-radius: 14px;
    font-size: 0.85rem;
    font-weight: 900;
    margin-top: 1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.signal-bullish {
    background: rgba(52, 211, 153, 0.2);
    color: var(--neon-green);
    border: 1px solid rgba(52, 211, 153, 0.4);
    box-shadow: 0 0 20px rgba(52, 211, 153, 0.3);
}

.signal-neutral {
    background: rgba(251, 191, 36, 0.2);
    color: var(--neon-amber);
    border: 1px solid rgba(251, 191, 36, 0.4);
}

.signal-bearish {
    background: rgba(248, 113, 113, 0.2);
    color: var(--neon-red);
    border: 1px solid rgba(248, 113, 113, 0.4);
    box-shadow: 0 0 20px rgba(248, 113, 113, 0.3);
}

/* ══════════════════════════════════════════ */
/* 🔄 REFRESH BAR - Animated */
/* ══════════════════════════════════════════ */
.refresh-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 10px 24px;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.refresh-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--neon-green);
    animation: pulse-glow 2s infinite;
    box-shadow: 0 0 15px var(--neon-green);
}

@keyframes pulse-glow {
    0%, 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 15px var(--neon-green); }
    50% { opacity: 0.5; transform: scale(1.4); box-shadow: 0 0 25px var(--neon-green); }
}

/* ══════════════════════════════════════════ */
/* ⏱️ TIMELINE - Sleek & Modern */
/* ══════════════════════════════════════════ */
.timeline {
    display: flex;
    flex-direction: column;
    gap: 0;
}

.tl-item {
    display: flex;
    align-items: flex-start;
    gap: 18px;
    padding: 1.2rem 0;
    border-bottom: 1px solid var(--border);
    font-size: 0.9rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tl-item:hover {
    background: var(--surface);
    margin: 0 -1.5rem;
    padding: 1.2rem 1.5rem;
    border-radius: 16px;
}

.tl-item:last-child {
    border-bottom: none;
}

.tl-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-muted);
    min-width: 100px;
    flex-shrink: 0;
    padding-top: 3px;
}

.tl-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
}

.tl-content {
    flex: 1;
    min-width: 0;
}

.tl-title {
    font-weight: 800;
    color: var(--text-primary);
}

.tl-desc {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-top: 4px;
    line-height: 1.7;
}

.tl-dir {
    font-size: 0.75rem;
    font-weight: 900;
    padding: 5px 14px;
    border-radius: 10px;
    flex-shrink: 0;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.tl-dir.up {
    background: rgba(52, 211, 153, 0.2);
    color: var(--neon-green);
    border: 1px solid rgba(52, 211, 153, 0.4);
}

.tl-dir.down {
    background: rgba(248, 113, 113, 0.2);
    color: var(--neon-red);
    border: 1px solid rgba(248, 113, 113, 0.4);
}

/* ══════════════════════════════════════════ */
/* 📖 GUIDE BOX */
/* ══════════════════════════════════════════ */
.guide-box {
    background: var(--surface);
    backdrop-filter: blur(40px);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.4rem 1.8rem;
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 2;
    margin-top: 1rem;
}

.guide-box strong {
    color: var(--text-primary);
    font-weight: 800;
}

/* ══════════════════════════════════════════ */
/* 🎬 FOOTER */
/* ══════════════════════════════════════════ */
.app-footer {
    margin-top: 3rem;
    padding: 1.5rem 0;
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
}

/* ══════════════════════════════════════════ */
/* 🎛️ CONTROLS & COMMON ELEMENTS */
/* ══════════════════════════════════════════ */
div[data-testid="stMetric"] {
    display: none;
}

footer {
    display: none !important;
}

.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stRadio label {
    color: var(--text-secondary) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

[data-testid="stHorizontalBlock"] {
    gap: 1rem !important;
}

.stSelectbox {
    margin-bottom: -0.3rem !important;
}

/* Custom Select Styling */
div[data-baseweb="select"] {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-radius: 14px !important;
    transition: all 0.3s !important;
}

div[data-baseweb="select"]:hover {
    border-color: var(--border-strong) !important;
    box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.3) !important;
}

/* Plotly 차트 */
.js-plotly-plot, .plotly, .js-plotly-plot .plotly,
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] > div,
.stPlotlyChart, .stPlotlyChart > div > div > div {
    touch-action: none !important;
    -webkit-touch-callout: none;
}
[data-testid="stPlotlyChart"] {
    width: 100% !important;
}

/* Modebar 스타일 */
.modebar { 
    opacity: 1 !important;
    top: 0px !important;
    right: 0px !important;
    bottom: auto !important;
    left: auto !important;
    background: transparent !important;
}
.modebar-btn { font-size: 15px !important; }
.modebar-group { 
    padding: 0 4px !important; 
    background: rgba(26, 31, 66, 0.8); 
    border-radius: 4px; 
    border: 1px solid var(--border);
}

/* ══════════════════════════════════════════ */
/* 📱 RESPONSIVE */
/* ══════════════════════════════════════════ */
@media (max-width: 768px) {
    .block-container {
        padding: 1.5rem 1.5rem 2rem 1.5rem !important;
    }
    
    .kpi-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
    }
    
    .page-header {
        padding: 1.5rem;
    }
    
    .card {
        padding: 1.5rem;
    }
    
    .report-box {
        padding: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📌 설정 및 상수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 차트 컬러 (다크 모드)
C = {
    "bg": "#0a0e27",          # 배경
    "grid": "#1e293b",        # 그리드
    "text": "#cbd5e1",        # 텍스트
    "candle_up": "#34d399",   # 상승 캔들 (네온 그린)
    "candle_down": "#f87171", # 하락 캔들 (네온 레드)
    "ma20": "#fbbf24",        # MA20 (네온 앰버)
    "ma60": "#60a5fa",        # MA60 (네온 블루)
    "ma120": "#a78bfa",       # MA120 (네온 퍼플)
    "volume": "#475569",      # 거래량
    "liquidity": "#60a5fa",   # 유동성 (네온 블루)
    "recession": "#1e293b",   # 리세션
    "event": "#94a3b8",       # 이벤트
}

# 플롯리 기본 레이아웃 (다크 모드)
BASE_LAYOUT = dict(
    paper_bgcolor=C["bg"],
    plot_bgcolor=C["bg"],
    font=dict(family="JetBrains Mono, Inter, sans-serif", size=11, color=C["text"]),
    margin=dict(l=10, r=10, t=40, b=10),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(26, 31, 66, 0.95)",
        font_size=12,
        font_family="JetBrains Mono, monospace",
        bordercolor="rgba(96, 165, 250, 0.5)"
    ),
)

def ax(extra=None):
    """축 기본 스타일 (다크 모드)"""
    base = dict(
        showgrid=True,
        gridcolor=C["grid"],
        gridwidth=0.5,
        zeroline=False,
        showline=True,
        linecolor=C["grid"],
        linewidth=1,
        mirror=False,
        tickfont=dict(color=C["text"], size=10, family="JetBrains Mono, monospace"),
    )
    if extra:
        base.update(extra)
    return base

# 리세션 음영 함수
def add_recession(fig, df, is_subplot=False):
    """미국 경기침체 기간 음영 표시"""
    RECESSIONS = [
        ("2001-03-01", "2001-11-30"),
        ("2007-12-01", "2009-06-30"),
        ("2020-02-01", "2020-04-30"),
    ]
    for start, end in RECESSIONS:
        s_dt, e_dt = pd.to_datetime(start), pd.to_datetime(end)
        if s_dt > df.index.max() or e_dt < df.index.min():
            continue
        fig.add_vrect(
            x0=s_dt, x1=e_dt,
            fillcolor=C["recession"], opacity=0.15,
            layer="below", line_width=0,
            row="all" if is_subplot else None, col=1 if is_subplot else None
        )

# 국가 및 지수 설정
INDEX_CONFIG = {
    "🇺🇸 미국": {
        "나스닥 × WALCL": {
            "idx_ticker": "^IXIC", "idx_name": "나스닥종합지수", 
            "liq_ticker": "WALCL", "liq_label": "Fed 본원통화", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []  # 나중에 추가
        },
        "나스닥 × RRPONTSYD": {
            "idx_ticker": "^IXIC", "idx_name": "나스닥종합지수", 
            "liq_ticker": "RRPONTSYD", "liq_label": "역레포 잔액", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
        "나스닥 × M2SL": {
            "idx_ticker": "^IXIC", "idx_name": "나스닥종합지수", 
            "liq_ticker": "M2SL", "liq_label": "통화량 M2", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
        "S&P 500 × WALCL": {
            "idx_ticker": "^GSPC", "idx_name": "S&P 500", 
            "liq_ticker": "WALCL", "liq_label": "Fed 본원통화", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
        "S&P 500 × RRPONTSYD": {
            "idx_ticker": "^GSPC", "idx_name": "S&P 500", 
            "liq_ticker": "RRPONTSYD", "liq_label": "역레포 잔액", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
        "S&P 500 × M2SL": {
            "idx_ticker": "^GSPC", "idx_name": "S&P 500", 
            "liq_ticker": "M2SL", "liq_label": "통화량 M2", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
    },
    "🇰🇷 한국": {
        "KOSPI × WALCL": {
            "idx_ticker": "^KS11", "idx_name": "KOSPI", 
            "liq_ticker": "WALCL", "liq_label": "Fed 본원통화", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
        "KOSDAQ × WALCL": {
            "idx_ticker": "^KQ11", "idx_name": "KOSDAQ", 
            "liq_ticker": "WALCL", "liq_label": "Fed 본원통화", 
            "liq_prefix": "$", "liq_suffix": "B", 
            "data_src": "FRED · Yahoo Finance",
            "events": []
        },
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 주요 이벤트 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    # 2015
    ("2015-08-24", "중국발 블랙먼데이",       "위안 절하·중국 증시 폭락 → 글로벌 동반 급락 -3.9%",   "🇨🇳", "down"),
    # 2016
    ("2016-02-11", "유가 폭락 바닥",         "WTI $26 → 에너지·은행주 바닥 형성, S&P 1,829",       "🛢️", "down"),
    ("2016-06-23", "브렉시트 투표",          "영국 EU 탈퇴 결정 → 이틀간 -5.3% 후 빠른 회복",       "🇬🇧", "down"),
    ("2016-11-08", "트럼프 1기 당선",        "감세 기대 → 리플레이션 랠리",                         "🗳️", "up"),
    # 2017
    ("2017-12-22", "TCJA 감세법 서명",       "법인세 35→21% 인하, 기업이익 급증",                   "📝", "up"),
    # 2018
    ("2018-02-05", "VIX 폭발 (볼마겟돈)",    "변동성 상품 붕괴 → 하루 -4%, XIV 청산",               "💣", "down"),
    ("2018-10-01", "미중 무역전쟁 격화",      "관세 확대 → 불확실성 급등, Q4 -14%",                  "⚔️", "down"),
    ("2018-12-24", "파월 피벗",              "금리 인상 중단 시사 → 크리스마스 랠리",                "🔄", "up"),
    # 2019
    ("2019-07-31", "첫 금리인하 (10년만)",    "보험적 인하 25bp → 경기 확장 연장",                   "📉", "up"),
    ("2019-09-17", "레포 시장 위기",          "단기자금 금리 10% 급등 → 긴급 유동성 공급",            "🏧", "down"),
    # 2020
    ("2020-02-20", "코로나19 팬데믹 시작",    "글로벌 봉쇄 → -34% 역대급 폭락",                     "🦠", "down"),
    ("2020-03-23", "무제한 QE 선언",         "Fed 무한 양적완화 → V자 반등 시작",                   "💵", "up"),
    ("2020-11-09", "화이자 백신 발표",        "코로나 백신 성공 → 가치주·소형주 대전환 랠리",         "💉", "up"),
    # 2021
    ("2021-11-22", "인플레 피크 & 긴축 예고", "CPI 7%대, 테이퍼링 예고 → 성장주 하락 전환",           "📉", "down"),
    # 2022
    ("2022-01-26", "Fed 매파 전환",          "'곧 금리 인상' 시사 → 나스닥 -15%",                   "🦅", "down"),
    ("2022-02-24", "러-우 전쟁 개전",         "에너지 위기 → 스태그플레이션 공포",                    "💥", "down"),
    ("2022-03-16", "긴축 사이클 개시",        "첫 25bp 인상 → 11회 연속 인상 시작, 총 525bp",         "⬆️", "down"),
    ("2022-06-13", "S&P 약세장 진입",        "고점 대비 -20% 돌파, 빅테크 폭락",                     "🐻", "down"),
    ("2022-10-13", "CPI 피크아웃",           "인플레 둔화 확인 → 하락장 바닥 형성",                  "📊", "up"),
    ("2022-11-30", "ChatGPT 출시",          "생성형 AI 시대 개막 → AI 투자 광풍의 기폭제",           "🧠", "up"),
    # 2023
    ("2023-01-19", "S&P 강세장 전환",        "전고점 돌파 → 공식 강세장 진입",                       "🐂", "up"),
    ("2023-03-12", "SVB 은행 위기",          "실리콘밸리은행 파산 → 긴급 유동성 투입(BTFP)",          "🏦", "down"),
    ("2023-10-27", "금리 고점 공포",          "10년물 5% 돌파 → S&P 200일선 이탈",                   "📈", "down"),
    # 2024
    ("2024-02-22", "NVIDIA 실적 서프라이즈",   "AI 매출 폭증 → 시총 $2T 돌파, AI 랠리 가속",          "🚀", "up"),
    ("2024-08-05", "엔 캐리트레이드 청산",     "일본 금리인상 → 글로벌 디레버리징, VIX 65",            "🇯🇵", "down"),
    ("2024-09-18", "연준 빅컷 (50bp)",       "금리인하 사이클 개시, 소형주 급등",                    "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선",         "감세·규제완화 기대 → 지수 역대 신고가",                "🗳️", "up"),
    # 2025
    ("2025-01-27", "DeepSeek AI 쇼크",       "중국 저비용 AI 모델 → 반도체주 폭락 (NVDA -17%)",     "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세",    "전방위 관세 발표 → 이틀간 -10%, VIX 60",              "🚨", "down"),
    ("2025-04-09", "관세 90일 유예",          "트럼프 관세 일시중단 → 역대급 반등 +9.5%",             "🕊️", "up"),
    ("2025-05-12", "미중 제네바 관세 합의",    "상호관세 125→10% 인하 → S&P +3.2%, 무역전쟁 완화",    "🤝", "up"),
    ("2025-07-04", "OBBBA 법안 통과",        "감세 연장·R&D 비용처리 → 기업이익 전망 상향",           "📜", "up"),
    ("2025-10-29", "QT 종료 발표",           "12/1부터 대차대조표 축소 중단",                       "🛑", "up"),
    ("2025-12-11", "RMP 국채매입 재개",       "준비금 관리 매입 개시 → 유동성 확장 전환",              "💰", "up"),
    # 2026
    ("2026-01-28", "S&P 7000 돌파",          "14개월 만에 +1,000pt, AI 슈퍼사이클 & OBBBA 효과",    "🏆", "up"),
]

MARKET_PIVOTS_KR = [
    # 2015
    ("2015-08-24", "중국발 블랙먼데이",       "위안 절하 → KOSPI 1,830선 붕괴, 외국인 대량 매도",     "🇨🇳", "down"),
    # 2016
    ("2016-11-08", "트럼프 1기 당선",        "신흥국 자금유출 우려 → KOSPI 2,000선 하회",           "🗳️", "down"),
    ("2016-12-09", "박근혜 탄핵 가결",        "정치 불확실성 해소 기대 → 증시 반등",                 "⚖️", "up"),
    # 2017
    ("2017-05-10", "문재인 정부 출범",        "경제민주화·소득주도 성장 정책 → KOSPI 2,300 돌파",     "🏛️", "up"),
    # 2018
    ("2018-02-09", "반도체 슈퍼사이클 피크",   "메모리 가격 고점 → IT 업황 둔화 우려",                "💾", "down"),
    ("2018-10-11", "美中 무역전쟁 충격",      "대중 수출 타격 우려 → KOSPI -15%",                  "⚔️", "down"),
    # 2019
    ("2019-07-01", "일본 반도체 소재 수출제한", "3대 핵심 소재 규제 → 공급망 위기",                "🇯🇵", "down"),
    ("2019-10-23", "반도체 업황 회복 기대",    "삼성전자 실적 개선 → 외국인 순매수 전환",             "💻", "up"),
    # 2020
    ("2020-03-19", "코로나19 패닉",         "KOSPI 1,457까지 폭락 → 사상 최대 낙폭",              "🦠", "down"),
    ("2020-08-31", "KOSPI 2,400 돌파",     "개인·외국인 동반 매수 → 코로나 저점 대비 +65%",       "📈", "up"),
    # 2021
    ("2021-06-14", "KOSPI 3,266 사상 최고가", "반도체·2차전지 호황 → 역대 고점 경신",              "🏆", "up"),
    ("2021-12-03", "긴축 공포 하락 전환",     "Fed 테이퍼링 가속 → 외국인 매도세 지속",              "📉", "down"),
    # 2022
    ("2022-06-16", "KOSPI 2,300 붕괴",     "긴축·경기침체 공포 → 연저점 2,278",                  "🐻", "down"),
    ("2022-10-05", "저점 형성",             "원/달러 1,440원 고점 후 환율 안정화 → 반등 계기",      "📊", "up"),
    # 2023
    ("2023-01-27", "실적 회복 랠리",         "반도체 재고조정 마무리 → KOSPI 2,500 회복",          "🚀", "up"),
    ("2023-10-27", "중동발 리스크",          "이스라엘·하마스 전쟁 → 안전자산 선호, KOSPI -3%",      "💥", "down"),
    # 2024
    ("2024-04-10", "총선 여소야대 확정",      "정국 불확실성 → 외국인 투심 약화",                    "🗳️", "down"),
    ("2024-08-05", "글로벌 디레버리징",       "엔 캐리 청산 → KOSPI 2,600선 급락",                 "🇯🇵", "down"),
    # 2025
    ("2025-01-27", "DeepSeek 반도체 충격",   "SK하이닉스 -12%, 삼성전자 -8% → HBM 수요 우려",      "🤖", "down"),
    ("2025-04-09", "美관세 유예 반등",        "KOSPI +5.8% 급등 → 수출주 동반 강세",               "🕊️", "up"),
]

# 이벤트 목록을 INDEX_CONFIG에 할당
for ctry, indexes in INDEX_CONFIG.items():
    events = MARKET_PIVOTS if ctry == "🇺🇸 미국" else MARKET_PIVOTS_KR
    for idx_name, idx_cfg in indexes.items():
        idx_cfg["events"] = events


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 데이터 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=3600)
def load_data(idx_ticker, liq_ticker):
    """지수 + 유동성 + OHLC 데이터 로드 (캐시 1시간)"""
    start_date = "2000-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    # ━━ 1) 지수 종가 데이터 (pandas_datareader) ━━
    try:
        idx_df = web.DataReader(idx_ticker, "yahoo", start_date, end_date)["Close"].to_frame("SP500")
        idx_df.index = pd.to_datetime(idx_df.index).normalize()
    except Exception:
        st.error(f"⚠️ 지수 데이터({idx_ticker}) 로드 실패")
        return None, None
    
    # ━━ 2) 유동성 데이터 (FRED) ━━
    try:
        liq_df = web.DataReader(liq_ticker, "fred", start_date, end_date)
        liq_df.columns = ["Liquidity"]
        liq_df.index = pd.to_datetime(liq_df.index).normalize()
    except Exception:
        st.error(f"⚠️ 유동성 데이터({liq_ticker}) 로드 실패")
        return None, None
    
    # ━━ 3) OHLC 데이터 (yfinance) ━━
    try:
        import yfinance as yf
        ohlc = yf.download(idx_ticker, start=start_date, end=end_date, progress=False)
        if isinstance(ohlc.columns, pd.MultiIndex):
            ohlc.columns = ohlc.columns.droplevel(1)
        ohlc = ohlc[["Open", "High", "Low", "Close", "Volume"]].copy()
        ohlc.index = pd.to_datetime(ohlc.index).normalize()
        ohlc_raw = ohlc.copy()
    except Exception:
        st.error(f"⚠️ OHLC 데이터({idx_ticker}) 로드 실패")
        return None, None
    
    # ━━ 4) 병합 (지수 + 유동성) ━━
    df = idx_df.join(liq_df, how="left")
    df["Liquidity"] = df["Liquidity"].ffill()
    df = df.dropna(subset=["SP500", "Liquidity"])
    
    # ━━ 5) 파생 지표 ━━
    df["Liq_MA"] = df["Liquidity"].rolling(20, min_periods=1).mean()
    df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
    df["SP_YoY"] = df["SP500"].pct_change(252) * 100
    df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])
    
    return df, ohlc_raw


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 UI 레이아웃
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 헤더
st.markdown(
    """
    <div class="page-header">
        <div class="page-header-icon">📈</div>
        <div>
            <div class="page-title">유동성 × 시장 분석기</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    '<div class="page-desc">금융시장 유동성과 주요 지수의 상관관계를 실시간으로 분석하는 프로페셔널 대시보드</div>',
    unsafe_allow_html=True
)

# 새로고침 바
st.markdown(
    f"""
    <div class="refresh-bar">
        <div class="refresh-dot"></div>
        <span>다음 자동 갱신</span>
        <strong>{NEXT_REFRESH_TIME.strftime('%m/%d %H:%M KST')}</strong>
    </div>
    """,
    unsafe_allow_html=True
)

# 컨트롤 패널
col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1, 1])

with col1:
    country = st.selectbox("국가", list(INDEX_CONFIG.keys()), index=0)

with col2:
    idx_combo_list = list(INDEX_CONFIG[country].keys())
    idx_combo = st.selectbox("지수 × 유동성 조합", idx_combo_list, index=0)

with col3:
    cutoff = st.selectbox(
        "기간",
        ["2020-01-01", "2018-01-01", "2015-01-01", "2010-01-01", "2000-01-01"],
        index=2,
        format_func=lambda x: {
            "2020-01-01": "5년",
            "2018-01-01": "7년",
            "2015-01-01": "10년",
            "2010-01-01": "15년",
            "2000-01-01": "전체"
        }[x]
    )

with col4:
    tf = st.selectbox("캔들 주기", ["일봉", "주봉", "월봉"], index=0)

with col5:
    show_events = st.checkbox("이벤트", value=True)

# 선택된 설정
CC = INDEX_CONFIG[country][idx_combo]
idx_name = CC["idx_name"]

# 컨테이너 (레이아웃 구조)
kpi_container = st.container()
brief_container = st.container()
chart_container = st.container()

# 데이터 로드
with st.spinner("📊 데이터 로딩 중..."):
    df, ohlc_raw = load_data(CC["idx_ticker"], CC["liq_ticker"])

if df is None or ohlc_raw is None:
    st.stop()

# 자동 이벤트 탐지
def detect_auto_events(ohlc, base_events, threshold=0.04):
    """일간 변동률이 threshold 이상인 날을 자동 탐지"""
    auto = []
    existing_dates = {pd.to_datetime(e[0]).date() for e in base_events}
    ret = ohlc["Close"].pct_change()
    for dt_idx in ohlc.index:
        if pd.isna(ret.loc[dt_idx]) or dt_idx.date() in existing_dates:
            continue
        if abs(ret.loc[dt_idx]) < threshold:
            continue
        pct = ret.loc[dt_idx] * 100
        if ret.loc[dt_idx] > 0:
            auto.append((dt_idx.strftime("%Y-%m-%d"),
                f"급등 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "🔥", "up"))
        else:
            auto.append((dt_idx.strftime("%Y-%m-%d"),
                f"급락 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "⚡", "down"))
        existing_dates.add(dt_idx.date())
    return auto

BASE_EVENTS = CC["events"]
AUTO_EVENTS = detect_auto_events(ohlc_raw, BASE_EVENTS)
ALL_EVENTS = sorted(BASE_EVENTS + AUTO_EVENTS, key=lambda x: x[0])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI 카드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with kpi_container:
    latest = df.dropna(subset=["Liquidity", "SP500"]).iloc[-1]
    liq_val = latest["Liquidity"]
    sp_val = latest["SP500"]
    liq_yoy = latest["Liq_YoY"] if pd.notna(latest.get("Liq_YoY")) else 0
    sp_yoy = latest["SP_YoY"] if pd.notna(latest.get("SP_YoY")) else 0
    corr_val = df["Corr_90d"].dropna().iloc[-1] if len(df["Corr_90d"].dropna()) > 0 else 0

    def delta_html(val):
        cls = "up" if val >= 0 else "down"
        arrow = "▲" if val >= 0 else "▼"
        return f'<div class="kpi-delta {cls}">{arrow} YoY {val:+.1f}%</div>'

    corr_cls = "up" if corr_val >= 0.3 else "down"
    corr_desc = "강한 양의 상관" if corr_val >= 0.5 else ("약한 양의 상관" if corr_val >= 0 else "음의 상관")

    liq_display = f"{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}"

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi blue">
            <div class="kpi-label">💵 {CC['liq_label']}</div>
            <div class="kpi-value">{liq_display}</div>
            {delta_html(liq_yoy)}
        </div>
        <div class="kpi red">
            <div class="kpi-label">📈 {idx_name}</div>
            <div class="kpi-value">{sp_val:,.0f}</div>
            {delta_html(sp_yoy)}
        </div>
        <div class="kpi green">
            <div class="kpi-label">🔗 90일 상관계수</div>
            <div class="kpi-value">{corr_val:.3f}</div>
            <div class="kpi-delta {corr_cls}">{corr_desc}</div>
        </div>
        <div class="kpi purple">
            <div class="kpi-label">📅 데이터 범위</div>
            <div class="kpi-value" style="font-size:1.05rem">{df.index.min().strftime('%Y.%m')} – {df.index.max().strftime('%Y.%m')}</div>
            <div class="kpi-delta up">{len(df):,}일</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Daily Brief
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with brief_container:
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    liq_3m = df["Liquidity"].dropna()
    liq_3m_chg = ((liq_3m.iloc[-1] - liq_3m.iloc[-63]) / liq_3m.iloc[-63] * 100) if len(liq_3m) > 63 else 0
    sp_1m = df["SP500"].dropna()
    sp_1m_chg = ((sp_1m.iloc[-1] - sp_1m.iloc[-21]) / sp_1m.iloc[-21] * 100) if len(sp_1m) > 21 else 0

    if corr_val > 0.5 and liq_3m_chg > 0:
        signal_class, signal_text = "signal-bullish", "🟢 유동성 확장 + 강한 상관 → 주가 상승 지지"
    elif corr_val < 0 or liq_3m_chg < -1:
        signal_class, signal_text = "signal-bearish", "🔴 유동성 수축 또는 상관 이탈 → 경계 필요"
    else:
        signal_class, signal_text = "signal-neutral", "🟡 혼합 시그널 → 방향성 주시"

    if country == "🇺🇸 미국":
        brief_policy = (
            '<strong>▎연준 정책 현황</strong><br>'
            '연방기금금리 <span class="hl">3.50–3.75%</span> 유지 (1/28 FOMC). '
            'QT는 12/1에 공식 종료되었으며, 12/12부터 <strong>준비금 관리 매입(RMP)</strong>을 통해 국채 매입을 재개하여 '
            '사실상 대차대조표 확장으로 전환했습니다. 파월 의장 임기 만료(5월)를 앞두고 '
            '케빈 워시(Kevin Warsh)가 차기 의장으로 지명되었으며, '
            '시장은 하반기 1~2회 추가 인하를 기대하고 있습니다.'
        )
        brief_liq = (
            f'<strong>▎유동성 데이터</strong><br>'
            f'본원통화 최신치 <span class="hl">{liq_display}</span> (YoY {liq_yoy:+.1f}%). '
            f'3개월 변화율 <span class="hl">{liq_3m_chg:+.1f}%</span>. '
            f'QT 종료와 RMP 개시로 유동성 바닥이 형성되었으며, 완만한 확장 추세에 진입했습니다.'
        )
        brief_market = (
            f'<strong>▎시장 반응</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> (1개월 {sp_1m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
            f'AI 슈퍼사이클과 OBBBA(감세 연장·R&D 비용처리) 재정부양이 주가를 지지하나, '
            f'높은 밸류에이션(CAPE ~39배)과 시장 집중도 심화가 리스크입니다.'
        )
    else:  # 한국
        brief_policy = (
            '<strong>▎한국은행 통화정책 현황</strong><br>'
            '기준금리 <span class="hl">2.50%</span> (2025/6 기준). '
            '글로벌 긴축 완화 흐름에 맞춰 한은도 인하 기조를 유지하고 있으며, '
            '원/달러 환율 안정과 가계부채 관리가 추가 인하의 핵심 변수입니다. '
            '수출 회복과 반도체 업황 개선이 경기 지지 요인입니다.'
        )
        brief_liq = (
            f'<strong>▎유동성 데이터</strong><br>'
            f'Fed 본원통화(글로벌 유동성 지표) 최신치 <span class="hl">{liq_display}</span> (YoY {liq_yoy:+.1f}%). '
            f'3개월 변화율 <span class="hl">{liq_3m_chg:+.1f}%</span>. '
            f'한국 증시는 미 달러 유동성에 높은 민감도를 보이며, Fed 정책 방향이 핵심 변수입니다.'
        )
        brief_market = (
            f'<strong>▎시장 반응</strong><br>'
            f'{idx_name} <span class="hl">{sp_val:,.0f}</span> (1개월 {sp_1m_chg:+.1f}%, YoY {sp_yoy:+.1f}%). '
            f'반도체 수출 호조와 AI 수혜 기대감이 시장을 지지하나, '
            f'미중 관세 리스크와 원화 약세, 코리아 디스카운트가 지속적 부담입니다.'
        )

    brief_corr = (
        f'<strong>▎상관관계 진단</strong><br>'
        f'90일 롤링 상관계수 <span class="hl">{corr_val:.3f}</span>. '
        + ('유동성과 주가가 강한 동행 관계를 유지 중입니다.' if corr_val > 0.5
           else '유동성-주가 동조성이 약화된 구간입니다.' if corr_val > 0
           else '음의 상관으로 전환된 특이 구간입니다.')
    )

    st.markdown(
        f'<div class="report-box">'
        f'<div class="report-header">'
        f'<span class="report-badge">Daily Brief</span>'
        f'<span class="report-date">{today_str} 기준</span></div>'
        f'<div class="report-title">📋 오늘의 유동성 &amp; 시장 브리핑</div>'
        f'<div class="report-body">'
        f'{brief_policy}'
        f'<hr class="report-divider">'
        f'{brief_liq}'
        f'<hr class="report-divider">'
        f'{brief_market}'
        f'<hr class="report-divider">'
        f'{brief_corr}'
        f'</div>'
        f'<div class="report-signal {signal_class}">{signal_text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인 차트 (캔들스틱 + 유동성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
dff = df[df.index >= pd.to_datetime(cutoff)].copy()

# 캔들스틱 OHLC 리샘플
def resample_ohlc(ohlc_df, rule):
    """OHLC를 주봉(W) 또는 월봉(ME)으로 리샘플"""
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W")
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
else:
    ohlc_chart = ohlc_filtered.copy()

# 이동평균
for ma_len in [20, 60, 120]:
    ohlc_chart[f"MA{ma_len}"] = ohlc_chart["Close"].rolling(ma_len).mean()

# 거래량 색상 (다크 모드)
vol_colors = [C["candle_down"] if c < o else C["candle_up"]
              for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]

st.markdown(
    f'<div class="card"><div class="card-title">'
    f'<span class="dot" style="background:{C["candle_up"]}"></span> '
    f'{idx_name} 차트 + {CC["liq_label"]} ({tf})</div></div>',
    unsafe_allow_html=True
)

fig_candle = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.02,
    row_heights=[0.75, 0.25],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# 유동성 (배경 영역)
liq_series = dff["Liq_MA"].dropna()
liq_hover_fmt = f"%{{y:,.0f}}{CC['liq_suffix']}<extra>{CC['liq_label']}</extra>"
fig_candle.add_trace(
    go.Scatter(
        x=liq_series.index,
        y=liq_series,
        name=f"{CC['liq_label']} ({CC['liq_prefix']})",
        fill="tozeroy",
        fillcolor="rgba(96, 165, 250, 0.1)",
        line=dict(color="rgba(96, 165, 250, 0.5)", width=2),
        hovertemplate=liq_hover_fmt
    ),
    row=1, col=1, secondary_y=True
)

# 캔들스틱
fig_candle.add_trace(
    go.Candlestick(
        x=ohlc_chart.index,
        open=ohlc_chart["Open"],
        high=ohlc_chart["High"],
        low=ohlc_chart["Low"],
        close=ohlc_chart["Close"],
        increasing_line_color=C["candle_up"],
        increasing_fillcolor=C["candle_up"],
        decreasing_line_color=C["candle_down"],
        decreasing_fillcolor=C["candle_down"],
        name=idx_name,
        whiskerwidth=0.3,
        increasing_line_width=1,
        decreasing_line_width=1,
    ),
    row=1, col=1
)

# 이동평균선
ma_colors = {"MA20": C["ma20"], "MA60": C["ma60"], "MA120": C["ma120"]}
for ma_name, ma_color in ma_colors.items():
    s = ohlc_chart[ma_name].dropna()
    if len(s) > 0:
        fig_candle.add_trace(
            go.Scatter(
                x=s.index,
                y=s,
                name=ma_name,
                line=dict(color=ma_color, width=1.5),
                hovertemplate="%{y:,.0f}<extra>" + ma_name + "</extra>"
            ),
            row=1, col=1
        )

# 거래량
fig_candle.add_trace(
    go.Bar(
        x=ohlc_chart.index,
        y=ohlc_chart["Volume"],
        name="거래량",
        marker_color=vol_colors,
        opacity=0.6,
        showlegend=False,
        hovertemplate="%{y:,.0f}<extra>Volume</extra>"
    ),
    row=2, col=1
)

# 이벤트 표시
if show_events:
    gap_map = {"일봉": 14, "주봉": 45, "월봉": 120}
    min_gap = gap_map.get(tf, 30)
    prev_dt = None
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max():
            continue
        if prev_dt and (dt - prev_dt).days < min_gap:
            continue
        prev_dt = dt
        
        fig_candle.add_vline(
            x=dt,
            line_width=1,
            line_dash="dot",
            line_color=C["event"],
            row="all",
            col=1
        )
        
        clr = C["candle_up"] if direction == "up" else C["candle_down"]
        fig_candle.add_annotation(
            x=dt,
            y=1.04,
            yref="paper",
            text=f"{emoji} {title}",
            showarrow=False,
            font=dict(size=10, color=clr),
            textangle=-35,
            xanchor="left"
        )

# 리세션 음영
add_recession(fig_candle, dff, True)

# 레이아웃 설정 (다크 모드)
liq_min_val = liq_series.min()
liq_max_val = liq_series.max()
liq_y_min = liq_min_val * 0.85
liq_y_max = liq_y_min + (liq_max_val - liq_y_min) / 0.6

fig_candle.update_layout(
    **BASE_LAYOUT,
    height=750,
    showlegend=True,
    legend=dict(
        yanchor="top",
        y=0.98,
        xanchor="left",
        x=0.01,
        font=dict(size=11, family="JetBrains Mono, monospace"),
        bgcolor="rgba(26, 31, 66, 0.8)",
        bordercolor="rgba(96, 165, 250, 0.3)",
        borderwidth=1
    ),
    xaxis_rangeslider_visible=False,
)

# 축 설정
fig_candle.update_xaxes(ax(), row=1, col=1)
fig_candle.update_xaxes(ax(), row=2, col=1)
fig_candle.update_yaxes(
    ax(dict(title=None, ticklabelposition="outside", automargin=True)),
    row=1, col=1, secondary_y=False
)
fig_candle.update_yaxes(
    ax(dict(
        title=None,
        title_font=dict(color=C["liquidity"]),
        tickfont=dict(color=C["liquidity"], size=10),
        showgrid=False,
        range=[liq_y_min, liq_y_max],
        ticklabelposition="outside",
        automargin=True
    )),
    row=1, col=1, secondary_y=True
)
fig_candle.update_yaxes(
    ax(dict(title=None, tickformat=".2s", fixedrange=True, ticklabelposition="outside", automargin=True)),
    row=2, col=1
)

# 차트 표시
st.plotly_chart(
    fig_candle,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": [
            "select2d", "lasso2d", "autoScale2d",
            "hoverClosestCartesian", "hoverCompareCartesian",
            "toggleSpikelines",
        ],
        "displaylogo": False,
        "responsive": True
    }
)

# 모바일 핀치 줌
st.markdown("""
<script>
document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {
    plot.style.touchAction = 'none';
    plot.addEventListener('touchstart', function(e) {}, {passive: false});
});
</script>
""", unsafe_allow_html=True)

# 최근 캔들 요약
if len(ohlc_chart) >= 2:
    last = ohlc_chart.iloc[-1]
    prev = ohlc_chart.iloc[-2]
    chg = (last["Close"] - prev["Close"]) / prev["Close"] * 100
    chg_arrow = "▲" if chg >= 0 else "▼"
    chg_color = "neon-green" if chg >= 0 else "neon-red"
    
    st.markdown(
        f'<div class="guide-box">'
        f'🕯️ <strong>최근 {tf}:</strong> '
        f'시 <strong>{last["Open"]:,.0f}</strong> · '
        f'고 <strong>{last["High"]:,.0f}</strong> · '
        f'저 <strong>{last["Low"]:,.0f}</strong> · '
        f'종 <strong>{last["Close"]:,.0f}</strong> '
        f'<span style="color:var(--{chg_color})">{chg_arrow} {abs(chg):.2f}%</span>'
        f'<br>'
        f'이평선: <span style="color:{C["ma20"]}">●</span> MA20 · '
        f'<span style="color:{C["ma60"]}">●</span> MA60 · '
        f'<span style="color:{C["ma120"]}">●</span> MA120 · '
        f'<span style="color:rgba(96,165,250,0.7)">파란 영역</span> = {CC["liq_label"]}'
        f'</div>',
        unsafe_allow_html=True
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 이벤트 타임라인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
event_count = sum(1 for d,_,_,_,_ in ALL_EVENTS if pd.to_datetime(d) >= dff.index.min())
st.markdown(
    f"""<div class="card">
        <div class="card-title">
            <span class="dot" style="background:{C['liquidity']}"></span>
            주요 매크로 이벤트 타임라인 ({event_count} 이벤트)
        </div>
    """,
    unsafe_allow_html=True
)

tl_html = '<div class="timeline">'
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    dt = pd.to_datetime(date_str)
    if dt < dff.index.min():
        continue
    dir_cls = "up" if direction == "up" else "down"
    dir_label = "상승" if direction == "up" else "하락"
    tl_html += f"""
    <div class="tl-item">
        <div class="tl-date">{date_str}</div>
        <div class="tl-icon">{emoji}</div>
        <div class="tl-content">
            <div class="tl-title">{title}</div>
            <div class="tl-desc">{desc}</div>
        </div>
        <div class="tl-dir {dir_cls}">{dir_label}</div>
    </div>"""
tl_html += "</div>"
st.markdown(tl_html + "</div>", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown(
    f'<div class="app-footer">'
    f'📊 데이터: {CC["data_src"]} · 업데이트: {df.index.max().strftime("%Y-%m-%d")}'
    f'<br>🔄 자동 갱신 4회/일 (PST·KST 09/18시) · 본 페이지는 투자 조언이 아닙니다'
    f'</div>',
    unsafe_allow_html=True
)