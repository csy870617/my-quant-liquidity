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
    page_title="유동성 × 시장 분석기 (Naver Style)", 
    page_icon="icon.png", 
    layout="wide"
)

# 로고 (있을 경우)
try:
    st.logo("icon.png")
except Exception:
    pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 자동 새로고침 (하루 4회: PST 09/18 + KST 09/18)
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
    local_next = next_t.astimezone(ZoneInfo("Asia/Seoul"))
    return local_next, secs

NEXT_REFRESH_TIME, REFRESH_SECS = get_next_refresh()
st.markdown(
    f'<meta http-equiv="refresh" content="{min(REFRESH_SECS, 3600)}">',
    unsafe_allow_html=True,
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CSS (네이버 금융 스타일 - 화이트/플랫)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');

:root {
    --bg-color: #ffffff;
    --border-color: #e0e0e0;
    --text-main: #333333;
    --text-sub: #666666;
    --up-color: #f04452; /* 네이버 상승 빨강 */
    --down-color: #3f60d6; /* 네이버 하락 파랑 */
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Noto Sans KR', 'Roboto', sans-serif;
    background-color: var(--bg-color) !important;
    color: var(--text-main);
}
[data-testid="stHeader"] { background: transparent !important; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px;
}

/* 헤더 스타일 */
.header-container {
    border-bottom: 2px solid #222;
    padding-bottom: 15px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
}
.page-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111;
    letter-spacing: -1px;
}
.update-info {
    font-size: 0.85rem;
    color: #888;
}

/* KPI 박스 스타일 (심플) */
.kpi-container {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
}
.kpi-box {
    flex: 1;
    border: 1px solid var(--border-color);
    padding: 15px;
    border-radius: 0; /* 네이버식 각진 디자인 */
    background: #fff;
}
.kpi-label {
    font-size: 0.8rem;
    color: var(--text-sub);
    margin-bottom: 5px;
}
.kpi-value {
    font-family: 'Roboto', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #111;
}
.kpi-delta {
    font-size: 0.85rem;
    font-weight: 500;
    margin-top: 5px;
}
.up { color: var(--up-color); }
.down { color: var(--down-color); }

/* 리포트 박스 */
.report-box {
    background-color: #f9f9f9;
    border: 1px solid var(--border-color);
    padding: 20px;
    margin-bottom: 20px;
    font-size: 0.9rem;
    line-height: 1.6;
}
.report-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 10px;
    color: #222;
}
.highlight {
    background-color: #fff;
    border: 1px solid #ddd;
    padding: 0 4px;
    font-weight: 600;
    color: #222;
}

/* 타임라인 테이블 스타일 */
.timeline-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
}
.timeline-table th {
    border-top: 2px solid #333;
    border-bottom: 1px solid #ccc;
    padding: 10px;
    text-align: left;
    background: #f8f8f8;
    font-weight: 600;
}
.timeline-table td {
    border-bottom: 1px solid #eee;
    padding: 10px;
    color: #444;
}
.timeline-date {
    font-family: 'Roboto', sans-serif;
    color: #666;
    font-weight: 500;
}

/* Streamlit 위젯 조정 */
div[data-testid="stSelectbox"] label { font-size: 0.85rem; font-weight: 600; }
div[data-testid="stToggle"] label { font-size: 0.85rem; font-weight: 600; }

/* 차트 영역 */
.chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    border-bottom: 1px solid #eee;
    padding-bottom: 5px;
}
.chart-title {
    font-weight: 700;
    font-size: 1.1rem;
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 & 이벤트 (기존 데이터 유지)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MARKET_PIVOTS = [
    ("2015-08-24", "중국발 블랙먼데이", "위안 절하·중국 증시 폭락", "🇨🇳", "down"),
    ("2016-02-11", "유가 폭락 바닥", "WTI $26 → 에너지·은행주 바닥", "🛢️", "down"),
    ("2016-06-23", "브렉시트 투표", "영국 EU 탈퇴 결정", "🇬🇧", "down"),
    ("2016-11-08", "트럼프 1기 당선", "감세 기대 → 리플레이션 랠리", "🗳️", "up"),
    ("2017-12-22", "TCJA 감세법 서명", "법인세 35→21% 인하", "📝", "up"),
    ("2018-02-05", "VIX 폭발 (볼마겟돈)", "변동성 상품 붕괴", "💣", "down"),
    ("2018-10-01", "미중 무역전쟁 격화", "관세 확대 → 불확실성 급등", "⚔️", "down"),
    ("2018-12-24", "파월 피벗", "금리 인상 중단 시사", "🔄", "up"),
    ("2019-07-31", "첫 금리인하", "보험적 인하 25bp", "📉", "up"),
    ("2019-09-17", "레포 시장 위기", "단기자금 금리 급등", "🏧", "down"),
    ("2020-02-20", "코로나19 팬데믹", "글로벌 봉쇄 → -34% 폭락", "🦠", "down"),
    ("2020-03-23", "무제한 QE 선언", "Fed 무한 양적완화", "💵", "up"),
    ("2020-11-09", "화이자 백신 발표", "코로나 백신 성공", "💉", "up"),
    ("2021-11-22", "인플레 피크 & 긴축", "CPI 7%대, 테이퍼링 예고", "📉", "down"),
    ("2022-01-26", "Fed 매파 전환", "'곧 금리 인상' 시사", "🦅", "down"),
    ("2022-02-24", "러-우 전쟁 개전", "에너지 위기", "💥", "down"),
    ("2022-03-16", "긴축 사이클 개시", "첫 25bp 인상", "⬆️", "down"),
    ("2022-06-13", "S&P 약세장 진입", "고점 대비 -20% 돌파", "🐻", "down"),
    ("2022-10-13", "CPI 피크아웃", "인플레 둔화 확인", "📊", "up"),
    ("2022-11-30", "ChatGPT 출시", "생성형 AI 시대 개막", "🧠", "up"),
    ("2023-01-19", "S&P 강세장 전환", "전고점 돌파", "🐂", "up"),
    ("2023-03-12", "SVB 은행 위기", "실리콘밸리은행 파산", "🏦", "down"),
    ("2023-10-27", "금리 고점 공포", "10년물 5% 돌파", "📈", "down"),
    ("2024-02-22", "NVIDIA 어닝 서프", "AI 매출 폭증", "🚀", "up"),
    ("2024-08-05", "엔 캐리 청산", "일본 금리인상 여파", "🇯🇵", "down"),
    ("2024-09-18", "연준 빅컷 (50bp)", "금리인하 사이클 개시", "✂️", "up"),
    ("2024-11-05", "트럼프 2기 당선", "감세·규제완화 기대", "🗳️", "up"),
    ("2025-01-27", "DeepSeek AI 쇼크", "중국 저비용 AI 충격", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "전방위 관세 발표", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "트럼프 관세 일시중단", "🕊️", "up"),
    ("2025-05-12", "미중 제네바 합의", "상호관세 인하", "🤝", "up"),
    ("2025-07-04", "OBBBA 법안 통과", "감세 연장·R&D 비용처리", "📜", "up"),
    ("2025-10-29", "QT 종료 발표", "대차대조표 축소 중단", "🛑", "up"),
    ("2025-12-11", "RMP 국채매입 재개", "유동성 확장 전환", "💰", "up"),
    ("2026-01-28", "S&P 7000 돌파", "AI 슈퍼사이클", "🏆", "up"),
]

MARKET_PIVOTS_KR = [
    ("2015-08-24", "중국발 블랙먼데이", "위안 절하 → KOSPI 급락", "🇨🇳", "down"),
    ("2016-11-08", "트럼프 1기 당선", "신흥국 자금유출 우려", "🗳️", "down"),
    ("2016-12-09", "박근혜 탄핵 가결", "정치 불확실성 해소", "⚖️", "up"),
    ("2017-05-10", "문재인 대통령 취임", "경기부양 기대", "🏛️", "up"),
    ("2017-09-03", "북한 6차 핵실험", "지정학 리스크", "🚀", "down"),
    ("2018-04-27", "남북 판문점 회담", "코리아 디스카운트 축소", "🤝", "up"),
    ("2018-10-01", "미중 무역전쟁 격화", "수출주 직격탄", "⚔️", "down"),
    ("2019-07-01", "일본 수출규제", "반도체 소재 수출 제한", "🇯🇵", "down"),
    ("2020-03-19", "코스피 서킷브레이커", "코로나 패닉", "🦠", "down"),
    ("2020-03-23", "한은 긴급 금리인하", "0.75%로 빅컷", "💵", "up"),
    ("2020-05-28", "동학개미운동", "개인투자자 대거 유입", "🐜", "up"),
    ("2020-11-09", "화이자 백신 발표", "수출주 회복 기대", "💉", "up"),
    ("2021-01-07", "KOSPI 3,000 돌파", "역사상 첫 3,000 안착", "🏆", "up"),
    ("2021-06-24", "KOSPI 3,300 최고", "글로벌 유동성 피크", "📈", "up"),
    ("2021-11-22", "긴축 예고", "성장주·소형주 급락", "📉", "down"),
    ("2022-02-24", "러-우 전쟁 개전", "에너지 수입국 타격", "💥", "down"),
    ("2022-06-23", "한은 빅스텝", "기준금리 인상 가속", "⬆️", "down"),
    ("2022-09-26", "KOSPI 2,200 붕괴", "강달러·긴축", "🐻", "down"),
    ("2022-11-30", "ChatGPT 출시", "반도체 반등 기대", "🧠", "up"),
    ("2023-01-30", "한은 금리 동결", "금리 인상 사이클 종료", "🔄", "up"),
    ("2023-05-30", "KOSPI 2,600 회복", "반도체 업황 회복 기대", "📊", "up"),
    ("2024-01-02", "밸류업 프로그램", "저PBR주 급등", "📋", "up"),
    ("2024-08-05", "엔 캐리 청산", "글로벌 디레버리징", "🇯🇵", "down"),
    ("2024-12-03", "윤석열 비상계엄", "정치 위기 → 급락", "🚨", "down"),
    ("2024-12-14", "윤석열 탄핵 가결", "불확실성 일부 해소", "⚖️", "up"),
    ("2025-01-27", "DeepSeek AI 쇼크", "삼성·SK하이닉스 급락", "🤖", "down"),
    ("2025-04-02", "Liberation Day 관세", "수출주 폭락", "🚨", "down"),
    ("2025-04-09", "관세 90일 유예", "반등 성공", "🕊️", "up"),
    ("2025-05-12", "미중 관세 합의", "무역 완화 기대", "🤝", "up"),
    ("2025-06-03", "한은 금리인하", "경기 부양 목적", "✂️", "up"),
]

COUNTRY_CONFIG = {
    "🇺🇸 미국": {
        "indices": {"NASDAQ": "^IXIC", "S&P 500": "^GSPC", "다우존스": "^DJI"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "fred_rec": "USREC",
        "liq_divisor": 1,
        "liq_label": "본원통화",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS,
        "data_src": "Federal Reserve (FRED) · Yahoo Finance",
    },
    "🇰🇷 대한민국": {
        "indices": {"KOSPI": "^KS11", "KOSDAQ": "^KQ11"},
        "default_idx": 0,
        "fred_liq": "BOGMBASE",
        "fred_rec": "USREC",
        "liq_divisor": 1,
        "liq_label": "글로벌 유동성 (Fed)",
        "liq_unit": "$B",
        "liq_prefix": "$",
        "liq_suffix": "B",
        "events": MARKET_PIVOTS_KR,
        "data_src": "Federal Reserve (FRED) · Yahoo Finance (KRX)",
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, fred_liq, fred_rec, liq_divisor):
    try:
        end_dt = datetime.now()
        fetch_start = end_dt - timedelta(days=365 * 14)

        # [A] FRED 데이터 (유동성)
        try:
            fred_codes = [fred_liq]
            if fred_rec:
                fred_codes.append(fred_rec)
            fred_df = web.DataReader(fred_codes, "fred", fetch_start, end_dt).ffill()
            if fred_rec:
                fred_df.columns = ["Liquidity", "Recession"]
            else:
                fred_df.columns = ["Liquidity"]
                fred_df["Recession"] = 0
            fred_df["Liquidity"] = fred_df["Liquidity"] / liq_divisor
        except Exception as e:
            st.error(f"FRED 데이터 로드 실패: {e}")
            return None, None

        # [B] 주가 지수 데이터 (yfinance - OHLC)
        try:
            import yfinance as yf
            yf_data = yf.download(ticker, start=fetch_start, end=end_dt, progress=False)
            
            if yf_data.empty:
                st.error("지수 데이터를 가져오지 못했습니다. (데이터가 비어있음)")
                return None, None
            
            if isinstance(yf_data.columns, pd.MultiIndex):
                idx_close = yf_data['Close'][[ticker]].rename(columns={ticker: 'SP500'})
                ohlc = yf_data[[('Open',ticker),('High',ticker),('Low',ticker),('Close',ticker),('Volume',ticker)]].copy()
                ohlc.columns = ['Open','High','Low','Close','Volume']
            else:
                idx_close = yf_data[['Close']].rename(columns={'Close': 'SP500'})
                ohlc = yf_data[['Open','High','Low','Close','Volume']].copy()
                
        except Exception as e:
            st.error(f"지수 데이터 로드 실패 (yfinance): {e}")
            return None, None

        # [C] 데이터 통합 및 가공
        df = pd.concat([fred_df, idx_close], axis=1).ffill()
        
        if 'SP500' in df.columns:
            df["Liq_MA"] = df["Liquidity"].rolling(10).mean()
            df["SP_MA"] = df["SP500"].rolling(10).mean()
            df["Liq_YoY"] = df["Liquidity"].pct_change(252) * 100
            df["SP_YoY"] = df["SP500"].pct_change(252) * 100
        else:
            st.error("데이터 통합 과정에서 주가 컬럼을 생성하지 못했습니다.")
            return None, None

        for c in ["Liquidity", "SP500"]:
            s = df[c].dropna()
            if len(s) > 0:
                df[f"{c}_norm"] = (df[c] - s.min()) / (s.max() - s.min()) * 100
        
        df["Corr_90d"] = df["Liquidity"].rolling(90).corr(df["SP500"])

        cut = end_dt - timedelta(days=365 * 12)
        df = df[df.index >= pd.to_datetime(cut)]
        ohlc = ohlc[ohlc.index >= pd.to_datetime(cut)]
        return df.dropna(subset=["SP500"]), ohlc.dropna(subset=["Close"])
        
    except Exception as e:
        st.error(f"⚠️ 시스템 오류: {str(e)}")
        return None, None

def detect_auto_events(ohlc_df, base_events, threshold=0.05):
    if ohlc_df is None or ohlc_df.empty or len(ohlc_df) < 2:
        return []
    daily_ret = ohlc_df["Close"].pct_change()
    existing_dates = {pd.to_datetime(d).date() for d, *_ in base_events}
    auto = []
    for dt_idx, ret in daily_ret.items():
        if pd.isna(ret) or dt_idx.date() in existing_dates:
            continue
        if abs(ret) < threshold:
            continue
        pct = ret * 100
        if ret > 0:
            auto.append((dt_idx.strftime("%Y-%m-%d"), f"급등 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "🔥", "up"))
        else:
            auto.append((dt_idx.strftime("%Y-%m-%d"), f"급락 {pct:+.1f}%", f"하루 {pct:+.1f}% 변동", "⚡", "down"))
        existing_dates.add(dt_idx.date())
    return auto

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헤더 영역
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
now_str = datetime.now().strftime("%Y.%m.%d %H:%M")
next_str = NEXT_REFRESH_TIME.strftime("%H:%M")

st.markdown(f"""
<div class="header-container">
    <div class="page-title">시장 유동성 분석 <span style="font-size:1rem; color:#666; font-weight:400;">(Liquidity × Index)</span></div>
    <div class="update-info">최근 갱신: {now_str} (다음: {next_str})</div>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 컨트롤 바
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1, 1])
with ctrl1:
    country = st.selectbox("국가 선택", list(COUNTRY_CONFIG.keys()), index=0)
CC = COUNTRY_CONFIG[country]
IDX_OPTIONS = CC["indices"]

if st.session_state.get("_prev_country") != country:
    st.session_state["_prev_country"] = country
    st.session_state["idx_select"] = list(IDX_OPTIONS.keys())[CC["default_idx"]]

with ctrl2:
    idx_name = st.selectbox("지수 선택", list(IDX_OPTIONS.keys()), key="idx_select")
    idx_ticker = IDX_OPTIONS[idx_name]
with ctrl3:
    period = st.selectbox("조회 기간", ["3년", "5년", "7년", "10년", "전체"], index=1)
with ctrl4:
    tf = st.selectbox("차트 주기", ["일봉", "주봉", "월봉"], index=1)
with ctrl5:
    show_events = st.toggle("이벤트 보기", value=True)

period_map = {"3년": 3, "5년": 5, "7년": 7, "10년": 10, "전체": 12}
period_years = period_map[period]
cutoff = datetime.now() - timedelta(days=365 * period_years)

with st.spinner("데이터 동기화 중..."):
    df, ohlc_raw = load_data(idx_ticker, CC["fred_liq"], CC["fred_rec"], CC["liq_divisor"])

if df is None or df.empty:
    st.stop()

BASE_EVENTS = CC["events"]
AUTO_EVENTS = detect_auto_events(ohlc_raw, BASE_EVENTS)
ALL_EVENTS = sorted(BASE_EVENTS + AUTO_EVENTS, key=lambda x: x[0])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KPI & 브리핑
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
latest = df.dropna(subset=["Liquidity", "SP500"]).iloc[-1]
liq_val = latest["Liquidity"]
sp_val = latest["SP500"]
liq_yoy = latest["Liq_YoY"] if pd.notna(latest.get("Liq_YoY")) else 0
sp_yoy = latest["SP_YoY"] if pd.notna(latest.get("SP_YoY")) else 0
corr_val = df["Corr_90d"].dropna().iloc[-1] if len(df["Corr_90d"].dropna()) > 0 else 0

def kpi_html(label, value, delta, is_pct=False):
    cls = "up" if delta >= 0 else "down"
    arrow = "▲" if delta >= 0 else "▼"
    delta_str = f"{arrow} {abs(delta):.1f}%"
    return f"""
    <div class="kpi-box">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-delta {cls}">{delta_str}</div>
    </div>
    """

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(kpi_html(CC['liq_label'], f"{CC['liq_prefix']}{liq_val:,.0f}{CC['liq_suffix']}", liq_yoy), unsafe_allow_html=True)
with col2:
    st.markdown(kpi_html(idx_name, f"{sp_val:,.0f}", sp_yoy), unsafe_allow_html=True)
with col3:
    c_cls = "up" if corr_val > 0 else "down"
    c_sign = "+" if corr_val > 0 else ""
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-label">유동성 상관계수 (90일)</div>
        <div class="kpi-value">{corr_val:.3f}</div>
        <div class="kpi-delta {c_cls}">{"강한 동조" if corr_val > 0.5 else "약한 동조" if corr_val > 0 else "역상관"}</div>
    </div>
    """, unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 네이버 금융 스타일 차트 구현
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown('<div class="chart-header"><span class="chart-title">종합 차트</span></div>', unsafe_allow_html=True)

# [데이터 준비]
dff = df[df.index >= pd.to_datetime(cutoff)].copy()
ohlc_filtered = ohlc_raw[ohlc_raw.index >= pd.to_datetime(cutoff)].copy()

def resample_ohlc(ohlc_df, rule):
    return ohlc_df.resample(rule).agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
    }).dropna()

if tf == "주봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "W-FRI") # 금요일 기준
elif tf == "월봉":
    ohlc_chart = resample_ohlc(ohlc_filtered, "ME")
else:
    ohlc_chart = ohlc_filtered.copy()

# 이평선 계산
for ma in [5, 20, 60, 120]:
    ohlc_chart[f"MA{ma}"] = ohlc_chart["Close"].rolling(ma).mean()

# 네이버 색상 정의
NAV_UP = "#ec4846"   # 상승 (빨강)
NAV_DN = "#3870c9"   # 하락 (파랑)
NAV_BG = "#ffffff"   # 배경
NAV_GRID = "#f4f4f4" # 그리드

# 거래량 색상 (전일 대비가 아닌 캔들 양/음 기준)
vol_colors = [NAV_UP if c >= o else NAV_DN for o, c in zip(ohlc_chart["Open"], ohlc_chart["Close"])]

# 서브플롯 (2행 1열, 하단 거래량)
fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.0,
    row_heights=[0.8, 0.2],
    specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
)

# [1] 유동성 영역 (Secondary Y) - 배경처럼 은은하게
liq_series = dff["Liq_MA"].dropna()
fig.add_trace(go.Scatter(
    x=liq_series.index, y=liq_series, 
    name=CC['liq_label'],
    fill='tozeroy', 
    fillcolor='rgba(100, 116, 139, 0.07)',
    line=dict(color='rgba(100, 116, 139, 0.3)', width=1),
    hovertemplate=f"%{{y:,.0f}}{CC['liq_suffix']}"
), row=1, col=1, secondary_y=True)

# [2] 캔들스틱 (네이버 스타일)
fig.add_trace(go.Candlestick(
    x=ohlc_chart.index,
    open=ohlc_chart["Open"], high=ohlc_chart["High"],
    low=ohlc_chart["Low"], close=ohlc_chart["Close"],
    increasing_line_color=NAV_UP, increasing_fillcolor=NAV_UP,
    decreasing_line_color=NAV_DN, decreasing_fillcolor=NAV_DN,
    name=idx_name,
    whiskerwidth=0.4
), row=1, col=1)

# [3] 이동평균선 (5:초록, 20:빨강, 60:주황, 120:보라) - 네이버 기본 유사
ma_styles = {
    5: "#56b56e", 20: "#ec4846", 60: "#f59e0b", 120: "#8b5cf6"
}
for ma, color in ma_styles.items():
    s = ohlc_chart[f"MA{ma}"].dropna()
    fig.add_trace(go.Scatter(
        x=s.index, y=s, name=f"{ma}일",
        line=dict(color=color, width=1),
        hoverinfo='skip'
    ), row=1, col=1)

# [4] 거래량
fig.add_trace(go.Bar(
    x=ohlc_chart.index, y=ohlc_chart["Volume"],
    marker_color=vol_colors,
    name="거래량",
    showlegend=False
), row=2, col=1)

# [5] 이벤트 마커
if show_events:
    gap_map = {"일봉": 14, "주봉": 50, "월봉": 120}
    min_gap = gap_map.get(tf, 30)
    prev_dt = None
    for date_str, title, _, emoji, direction in ALL_EVENTS:
        dt = pd.to_datetime(date_str)
        if dt < ohlc_chart.index.min() or dt > ohlc_chart.index.max(): continue
        if prev_dt and (dt - prev_dt).days < min_gap: continue
        prev_dt = dt
        
        # 세로 점선
        fig.add_vline(x=dt, line_width=1, line_dash="dot", line_color="#bbb", row="all", col=1)
        # 상단 아이콘
        fig.add_annotation(
            x=dt, y=1.02, yref="paper", text=emoji, showarrow=False,
            font=dict(size=14), row=1, col=1
        )

# 레이아웃 설정 (네이버 금융 모방)
fig.update_layout(
    plot_bgcolor=NAV_BG, paper_bgcolor=NAV_BG,
    margin=dict(t=30, b=0, l=0, r=10),
    hovermode="x unified",
    dragmode="pan",
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        font=dict(size=11, color="#333"), bgcolor="rgba(255,255,255,0)"
    ),
    # 하단 레인지 슬라이더 (미니맵)
    xaxis=dict(
        rangeslider=dict(visible=True, thickness=0.08, bgcolor="#fcfcfc"),
        type="date",
        showgrid=True, gridcolor=NAV_GRID,
        showline=True, linecolor="#e0e0e0",
        showspikes=True, spikethickness=1, spikecolor="#999", spikemode="across"
    ),
    xaxis2=dict(
        showgrid=True, gridcolor=NAV_GRID,
        showspikes=True, spikethickness=1, spikecolor="#999", spikemode="across"
    ),
    # Y축 (오른쪽 배치 - HTS 스타일)
    yaxis=dict(
        side="right", showgrid=True, gridcolor=NAV_GRID,
        tickformat=",", showline=True, linecolor="#e0e0e0",
        showspikes=True, spikethickness=1, spikecolor="#999", spikemode="across",
        fixedrange=False
    ),
    yaxis2=dict( # 거래량
        side="right", showgrid=False, showticklabels=False, fixedrange=True
    ),
    yaxis3=dict( # 유동성 (왼쪽 배치)
        overlaying="y", side="left", showgrid=False, showticklabels=True,
        tickfont=dict(color="#94a3b8", size=10),
        range=[liq_series.min()*0.9, liq_series.max()*1.1]
    )
)

st.plotly_chart(fig, use_container_width=True, config={
    "displayModeBar": False, "scrollZoom": True
})

# 모바일 터치 최적화
st.markdown("""
<script>
document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {
    plot.style.touchAction = 'none';
    plot.addEventListener('touchstart', function(e) {}, {passive: false});
});
</script>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 하단 이벤트 리스트 (테이블 형태)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("<br><h6>📌 주요 시장 이벤트 로그</h6>", unsafe_allow_html=True)

html = '<table class="timeline-table"><thead><tr><th>날짜</th><th>이벤트</th><th>영향</th></tr></thead><tbody>'
cnt = 0
for date_str, title, desc, emoji, direction in reversed(ALL_EVENTS):
    dt = pd.to_datetime(date_str)
    if dt < dff.index.min(): continue
    cnt += 1
    if cnt > 10: break # 최근 10개만
    
    color = "var(--up-color)" if direction == "up" else "var(--down-color)"
    html += f"""
    <tr>
        <td class="timeline-date">{date_str}</td>
        <td>
            <strong>{emoji} {title}</strong><br>
            <span style="font-size:0.8rem; color:#888;">{desc}</span>
        </td>
        <td style="color:{color}; font-weight:700;">{direction.upper()}</td>
    </tr>
    """
html += "</tbody></table>"
st.markdown(html, unsafe_allow_html=True)

# 푸터
st.markdown(
    f'<div style="margin-top:40px; text-align:center; font-size:0.8rem; color:#999;">'
    f'Data Source: {CC["data_src"]} | Developed with Streamlit'
    f'</div>',
    unsafe_allow_html=True
)