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

# 애플리케이션 제목
st.title("한국 주식 퀀트 분석기")

# 사용자 입력
symbol = st.text_input("종목명 또는 코드 입력", "")
year = st.number_input(
    "연도 입력",
    value=datetime.datetime.now().year,
    step=1
)
run_button = st.button("분석 시작")

if run_button:
    # 1) 종목 정보 조회
    with st.spinner("기업 정보 조회 중…"):
        info = find_corp_info(symbol)
        corp_code = info.get("corp_code")
        corp_name = info.get("corp_name")
    if not corp_code:
        st.error(f"❌ '{symbol}' 종목을 찾을 수 없습니다. 정확한 이름 또는 코드를 입력해 주세요.")
        st.stop()

    # 2) 데이터 수집
    data = get_combined_data(corp_code, year)
    price = data['price']
    pkrx = data['pykrx']

    # 3) 지표 계산
    metrics = calculate_metrics(data)

    # 4) 점수 계산
    score, detail, comment = calculate_score(metrics)

    # 2) 성장 지표 제외 안내 (개선사항 2)
    with st.expander("ℹ️ 성장 지표 제외 안내"):
        st.write(
            "- `RevenueGrowth`, `NetIncomeGrowth` 값이 음수 또는 없는 경우,\n"
            "  스코어 합산 대상에서 자동 제외됩니다."
        )

    # 5) 결과 출력 및 코멘트 분리 (개선사항 3)
    st.metric(label="종합 퀀트 점수", value=f"{score:.1f}")
    st.markdown(f"**평가:** {comment}")

    # 6) 시가총액 및 주요 값 표시
    st.subheader("주요 재무/펀더멘털 요약")
    col1, col2, col3 = st.columns(3)
    eps = pkrx.get('EPS', None)
    bps = pkrx.get('BPS', None)
    if not price.empty:
        mcap = price['시가총액'].iloc[-1] if '시가총액' in price.columns else price['종가'].iloc[-1] * pkrx.get('BPS', 0)
    else:
        mcap = None
    col1.metric("EPS (원)", f"{eps:.0f}" if eps else "N/A")
    col2.metric("BPS (원)", f"{bps:.0f}" if bps else "N/A")
    col3.metric("시가총액 (원)", f"{mcap:,.0f}" if mcap else "N/A")
