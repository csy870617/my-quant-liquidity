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

# 로고 (네이버 스타일 헤더 느낌을 위해 상단 로고는 심플하게 처리)
try:
    st.logo("icon.png")
except:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 로직
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def get_next_refresh():
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
    return next_t, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()
st.markdown(f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">', unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS (네이버 증권 스타일 + 모바일 최적화)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');

:root {
    --bg: #ffffff;
    --text-primary: #111111;
    --text-secondary: #767676;
    --up-color: #f73646;   /* 네이버 상승 빨강 */
    --down-color: #335eff; /* 네이버 하락 파랑 */
    --border: #ececec;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Pretendard', sans-serif;
    background: var(--bg) !important;
    color: var(--text-primary);
}
[data-testid="stHeader"] { background: transparent !important; }

/* 레이아웃 여백 조정 */
.block-container { 
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    max-width: 100%;
}

/* ── 네이버 스타일 헤더 ── */
.stock-header {
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
    margin-bottom: 10px;
}
.stock-name-row {
    display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px;
}
.stock-name {
    font-size: 1.4rem; font-weight: 800; color: #000;
}
.stock-ticker {
    font-size: 0.9rem; color: var(--text-secondary);
}
.stock-price-row {
    display: flex; align-items: baseline; gap: 10px;
}
.stock-price {
    font-family: 'Roboto Mono', sans-serif;
    font-size: 2.2rem; font-weight: 700; letter-spacing: -1px;
}
.stock-change {
    font-size: 1.1rem; font-weight: 600;
}
.c-up { color: var(--up-color); }
.c-down { color: var(--down-color); }
.c-flat { color: #333; }

/* ── 기간 선택 버튼 (라디오 버튼 스타일링) ── */
div[role="radiogroup"] {
    gap: 0 !important;
    background: #f4f5f7;
    padding: 3px;
    border-radius: 8px;
    display: flex;
    justify-content: space-between;
}
div[role="radiogroup"] label {
    flex: 1;
    text-align: center;
    border-radius: 6px;
    border: none !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #888 !important;
    background: transparent !important;
    padding: 6px 0 !important;
    margin: 0 !important;
}
/* 선택된 항목 스타일 (Streamlit 내부 클래스 타겟팅이 어려워 기본 동작에 의존하되 깔끔하게) */
div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
    display: none; /* 라디오 원형 숨김 */
}

/* ── Plotly 차트 (터치 최적화) ── */
[data-testid="stPlotlyChart"] { width: 100% !important; }
.js-plotly-plot .plotly, .js-plotly-plot .plotly div {
    touch-action: none !important; /* 핀치 줌 활성화 */
}

/* 툴바 커스텀 */
.modebar {
    opacity: 0.8 !important;
    top: 5px !important;
    right: 5px !important;
    background: rgba(255,255,255,0.8) !important;
    border-radius: 4px;
}

/* ── 하단 정보 박스 ── */
.info-box {
    background: #f9fafb; border: 1px solid #eee; border-radius: 12px;
    padding: 15px; margin-top: 15px; font-size: 0.9rem; color: #444; line-height: 1.6;
}
.info-label { font-weight: 700; color: #000; margin-bottom: 4px; display:block; }
.info-val { color: var(--text-secondary); }

/* 모바일 미디어 쿼리 */
@media (max-width: 768px) {
    .stock-price { font-size: 1.8rem; }
    .stock-name { font-size: 1.2rem; }
    .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 정의
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2024-11-05", "트럼프 당선", "감세 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek 쇼크", "AI 수익성 우려", "🤖", "down"),
    ("2025-04-09", "관세 유예", "무역전쟁 완화", "🕊️", "up"),
    ("2025-12-11", "RMP 재개", "유동성 확장", "💰", "up"),
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "liq_label": "본원통화",
        "events": MARKET_PIVOTS,
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "liq_label": "글로벌 유동성",
        "events": MARKET_PIVOTS,
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, fred_liq):
    try:
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365 * 11) # 넉넉하게

        # 주가 데이터
        import yfinance as yf
        yf_data = yf.download(ticker, start=start_dt, end=end_dt, progress=False)
        
        if isinstance(yf_data.columns, pd.MultiIndex):
            price = yf_data['Close'][[ticker]].rename(columns={ticker: 'Close'})
            ohlc = yf_data[[('Open',ticker),('High',ticker),('Low',ticker),('Close',ticker),('Volume',ticker)]].copy()
            ohlc.columns = ['Open','High','Low','Close','Volume']
        else:
            price = yf_data[['Close']]
            ohlc = yf_data[['Open','High','Low','Close','Volume']].copy()

        # 유동성 데이터 (FRED)
        try:
            liq = web.DataReader(fred_liq, "fred", start_dt, end_dt).ffill()
            liq.columns = ["Liquidity"]
        except:
            liq = pd.DataFrame(index=price.index, columns=["Liquidity"]) # 실패시 빈값

        # 데이터 병합
        df = pd.concat([price, liq], axis=1).ffill().dropna(subset=['Close'])
        
        # 이동평균선 계산
        for ma in [5, 20, 60, 120]:
            ohlc[f"MA{ma}"] = ohlc["Close"].rolling(window=ma).mean()
            
        return df, ohlc
    except Exception:
        return None, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI 구성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. 상단 컨트롤 (국가/지수 선택 - 네이버처럼 최소화)
c1, c2 = st.columns([1, 2])
with c1:
    country = st.selectbox("국가", list(COUNTRY_CONFIG.keys()), label_visibility="collapsed")
CC = COUNTRY_CONFIG[country]
with c2:
    idx_name = st.selectbox("지수", list(CC["indices"].keys()), label_visibility="collapsed")
    idx_ticker = CC["indices"][idx_name]

# 데이터 로드
df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"])

if df is None or df.empty:
    st.error("데이터 로드 실패")
    st.stop()

# 2. 헤더 정보 (현재가, 등락률 - 네이버 스타일)
last_close = ohlc_raw["Close"].iloc[-1]
prev_close = ohlc_raw["Close"].iloc[-2]
diff = last_close - prev_close
pct = (diff / prev_close) * 100

color_cls = "c-up" if diff > 0 else "c-down" if diff < 0 else "c-flat"
sign = "+" if diff > 0 else ""
arrow = "▲" if diff > 0 else "▼" if diff < 0 else "-"

st.markdown(f"""
<div class="stock-header">
    <div class="stock-name-row">
        <span class="stock-name">{idx_name}</span>
        <span class="stock-ticker">{idx_ticker}</span>
    </div>
    <div class="stock-price-row {color_cls}">
        <span class="stock-price">{last_close:,.2f}</span>
        <span class="stock-change">{arrow} {abs(diff):,.2f} ({sign}{pct:.2f}%)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 3. 기간 선택 버튼 (차트 바로 위)
# 네이버: 1일 1주 3월 1년 3년 10년
time_range = st.radio(
    "기간 선택", 
    ["1개월", "3개월", "1년", "3년", "10년"], 
    index=2, 
    horizontal=True,
    label_visibility="collapsed"
)

# 기간 필터링
end_date = df.index.max()
if time_range == "1개월": start_date = end_date - timedelta(days=30)
elif time_range == "3개월": start_date = end_date - timedelta(days=90)
elif time_range == "1년": start_date = end_date - timedelta(days=365)
elif time_range == "3년": start_date = end_date - timedelta(days=365*3)
else: start_date = end_date - timedelta(days=365*10)

chart_data = ohlc_raw[ohlc_raw.index >= start_date].copy()
liq_data = df[df.index >= start_date]["Liquidity"].copy()

# 4. 차트 그리기 (네이버 스타일: 빨강/파랑, Y축 오른쪽, 볼륨 하단)
fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.02, 
    row_heights=[0.8, 0.2],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# (1) 캔들스틱 (네이버 색상: 상승 Red, 하락 Blue)
fig.add_trace(go.Candlestick(
    x=chart_data.index,
    open=chart_data["Open"], high=chart_data["High"],
    low=chart_data["Low"], close=chart_data["Close"],
    increasing_line_color="#f73646", increasing_fillcolor="#f73646", # 네이버 상승 빨강
    decreasing_line_color="#335eff", decreasing_fillcolor="#335eff", # 네이버 하락 파랑
    name="주가",
    showlegend=False
), row=1, col=1)

# (2) 이동평균선 (5, 20, 60, 120)
ma_colors = {5: "#999", 20: "#f5a623", 60: "#33bb55", 120: "#aa55ff"}
for ma, color in ma_colors.items():
    if f"MA{ma}" in chart_data.columns:
        fig.add_trace(go.Scatter(
            x=chart_data.index, y=chart_data[f"MA{ma}"],
            mode='lines', line=dict(color=color, width=1),
            name=f"{ma}일",
            hoverinfo='skip' # 툴팁 간소화
        ), row=1, col=1)

# (3) 유동성 지표 (은은하게 배경에 깔기)
fig.add_trace(go.Scatter(
    x=liq_data.index, y=liq_data,
    name=CC["liq_label"],
    line=dict(color="rgba(100, 100, 100, 0.3)", width=1.5, dash='dot'),
    hovertemplate="%{y:,.0f} B",
), row=1, col=1, secondary_y=True)

# (4) 거래량 (하단 바 차트)
vol_colors = ["#f73646" if row.Close > row.Open else "#335eff" for i, row in chart_data.iterrows()]
fig.add_trace(go.Bar(
    x=chart_data.index, y=chart_data["Volume"],
    marker_color=vol_colors,
    name="거래량",
    showlegend=False
), row=2, col=1)

# (5) 레이아웃 설정 (네이버 스타일)
fig.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    margin=dict(t=10, b=10, l=10, r=50), # 오른쪽 여백 확보 (Y축용)
    height=500,
    hovermode="x unified",
    dragmode="pan", # 모바일 핀치 줌을 위해 pan 모드
    xaxis_rangeslider_visible=False,
    showlegend=True,
    legend=dict(
        orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
        font=dict(size=10, color="#666"), bgcolor="rgba(255,255,255,0.5)"
    )
)

# X축 설정 (날짜 포맷)
fig.update_xaxes(
    gridcolor="#f0f0f0", 
    showgrid=True, 
    tickformat="%Y.%m",
    row=1, col=1
)
fig.update_xaxes(
    gridcolor="#f0f0f0", 
    showgrid=True, 
    tickformat="%Y.%m",
    row=2, col=1
)

# Y축 설정 (오른쪽 배치 - 네이버 스타일)
fig.update_yaxes(
    side="right", # ★ 핵심: Y축 오른쪽
    gridcolor="#f0f0f0", 
    showgrid=True, 
    tickfont=dict(color="#333", size=11),
    ticklabelposition="outside",
    row=1, col=1, secondary_y=False
)
# 유동성 Y축 (왼쪽 숨김 처리하거나 보조로)
fig.update_yaxes(
    visible=False, 
    row=1, col=1, secondary_y=True
)
# 거래량 Y축 (오른쪽, 그리드 없음)
fig.update_yaxes(
    side="right",
    showgrid=False,
    tickformat=".2s",
    tickfont=dict(color="#999", size=10),
    row=2, col=1
)

# 툴바 설정
config = {
    'displayModeBar': True,
    'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines'],
    'displaylogo': False,
    'scrollZoom': True, # ★ 핀치 줌 활성화
}

st.plotly_chart(fig, use_container_width=True, config=config)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단 정보 (브리핑)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<div class="info-box">
    <span class="info-label">📢 Daily Market Brief</span>
    최근 시장은 미 연준의 정책 변화와 글로벌 유동성 흐름에 민감하게 반응하고 있습니다. 
    위 차트의 <span style="color:#aaa; font-weight:bold;">---- 점선</span>은 
    중앙은행의 유동성 공급 추이를 나타냅니다. 주가지수와 유동성의 상관관계를 통해 
    시장 방향성을 가늠해 보세요.
</div>
""", unsafe_allow_html=True)

# 자바스크립트: 모바일 터치 최적화 강제
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    var plot = document.querySelector('.js-plotly-plot');
    if (plot) {
        plot.style.touchAction = 'none';
    }
});
</script>
""", unsafe_allow_html=True)