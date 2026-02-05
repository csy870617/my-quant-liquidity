import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 페이지 설정 ---
st.set_page_config(page_title="Pure Liquidity Index", layout="wide")

@st.cache_data(ttl=3600) # 1시간마다 데이터 갱신
def get_pure_liquidity():
    # 데이터 수집 (최근 5년치로 자동 설정하여 '상대적 지수' 산출)
    end = datetime.now()
    start = end - timedelta(days=365 * 5)
    
    # WALCL(연준자산), WDTGAL(TGA), RRPONTSYD(역레포)
    symbols = {'WALCL': 'Fed_Assets', 'WDTGAL': 'TGA', 'RRPONTSYD': 'RRP'}
    df = web.DataReader(list(symbols.keys()), 'fred', start, end)
    df.columns = [symbols[col] for col in df.columns]
    
    # 순유동성 공식: Net Liquidity = Fed_Assets - TGA - RRP
    df['Net_Liquidity'] = df['Fed_Assets'] - df['TGA'] - df['RRP']
    return df.dropna()

def calculate_idx(series):
    # 현재 유동성이 최근 5년 범위 내에서 1~100 중 어디인지 산출
    min_val = series.min()
    max_val = series.max()
    curr_val = series.iloc[-1]
    return ((curr_val - min_val) / (max_val - min_val)) * 100

# --- 실행 로직 ---
st.title("🌊 실시간 순유동성(Net Liquidity) 분석기")
st.markdown("매니저의 주관을 배제하고 **연준 대차대조표 기반의 순수 유동성**만 측정합니다.")

try:
    data = get_pure_liquidity()
    current_index = calculate_idx(data['Net_Liquidity'])
    
    # 1. 메인 지표 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("현재 유동성 지수", f"{current_index:.1f} / 100")
    with col2:
        st.metric("실질 가용 자금", f"${data['Net_Liquidity'].iloc[-1] / 1000:.2f}T")
    with col3:
        st.write(f"최종 데이터 업데이트: {data.index[-1].date()}")

    # 2. 유동성 게이지 차트
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_index,
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 30], 'color': "#ff4b4b"},
                {'range': [30, 70], 'color': "#fdfd96"},
                {'range': [70, 100], 'color': "#00cc96"}]}))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # 3. 유동성 흐름 차트
    st.subheader("유동성 변화 추이 (최근 5년)")
    st.line_chart(data['Net_Liquidity'])

    # 4. 데이터 상세 설명
    with st.expander("산출 공식 및 데이터 설명"):
        st.latex(r"Net\ Liquidity = WALCL - TGA - RRP")
        st.write("- **WALCL:** 연준이 공급한 총 자산 (돈의 뿌리)")
        st.write("- **TGA:** 재무부 계좌 잔액 (정부가 묶어둔 돈, 시장에선 마이너스)")
        st.write("- **RRP:** 역레포 잔액 (시중 잉여 자금이 연준으로 회수된 돈, 시장에선 마이너스)")

except Exception as e:
    st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")