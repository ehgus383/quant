# app.py

import streamlit as st
import datetime
from utils import find_corp_info
from data_provider import get_combined_data
from metrics import calculate_metrics
from scorer import calculate_score

# Streamlit 페이지 설정
st.set_page_config(
    page_title="한국 주식 퀀트 분석기",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🇰🇷 한국 주식 퀀트 분석기 (DART + PyKrx)")

# 사이드바 입력
st.sidebar.header("분석 설정")
symbol = st.sidebar.text_input("종목명 또는 종목코드", value="삼성전자")
year = st.sidebar.number_input(
    "기준 연도",
    min_value=2000,
    max_value=datetime.datetime.now().year - 1,
    value=datetime.datetime.now().year - 1,
    step=1
)
run_button = st.sidebar.button("분석 실행")

# 캐시 데이터 함수
@st.cache_data(ttl=60*60)
def load_data(code: str, year: int) -> dict:
    return get_combined_data(code, year)

if run_button:
    # 1) 종목 정보 조회
    with st.spinner("기업 정보 조회 중…"):
        corp_code, corp_name = find_corp_info(symbol)
    if not corp_code:
        st.error(f"❌ '{symbol}' 종목을 찾을 수 없습니다. 정확한 이름 또는 코드를 입력해 주세요.")
    else:
        st.subheader(f"{corp_name} ({corp_code}) — {year}년 기준 분석 결과")

        # 2) 데이터 수집
        with st.spinner("재무 및 시세 데이터 수집 중…"):
            data = load_data(corp_code, year)
            dart = data['dart']      # {'bs','is','cf'} DataFrames
            price = data['price']    # OHLCV DataFrame
            pkrx = data['pykrx']     # fundamental dict

        # 3) 지표 계산
        with st.spinner("지표 계산 중…"):
            metrics = calculate_metrics(dart, price, pkrx)

        # 4) 점수화
        with st.spinner("점수 계산 중…"):
            score, comment, detail = calculate_score(metrics)

        # 5) 결과 출력
        st.metric(label="종합 퀀트 점수", value=f"{score:.1f}", delta=comment)
        st.markdown("---")

        # 지표별 세부 점수 테이블
        st.subheader("지표별 세부 점수 (0~100)")
        st.table(detail)

        # 지표별 분포 차트
        st.subheader("지표별 점수 분포")
        st.bar_chart(detail)

        # (추가) 시가총액 및 주요 값 표시
        st.subheader("주요 재무/펀더멘털 요약")
        col1, col2, col3 = st.columns(3)
        # 예시: 최신 EPS, BPS, 시가총액
        eps = pkrx.get('EPS', None)
        bps = pkrx.get('BPS', None)
        # 시가총액 계산
        if not price.empty:
            mcap = price['시가총액'][-1] if '시가총액' in price.columns else price['종가'][-1]*pkrx.get('BPS', 0)
        else:
            mcap = None
        col1.metric("EPS (원)", f"{eps:.0f}" if eps else "N/A")
        col2.metric("BPS (원)", f"{bps:.0f}" if bps else "N/A")
        col3.metric("시가총액 (원)", f"{mcap:,.0f}" if mcap else "N/A")
