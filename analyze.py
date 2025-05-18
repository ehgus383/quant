# analyze.py

import argparse
import logging
import sys
import datetime
import pandas as pd

from utils import find_corp_info
from data_provider import get_combined_data
from metrics import calculate_metrics
from scorer import calculate_score
from reporter import report_console

# 로거 설정
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def main():
    # 1) CLI 인자 파싱
    parser = argparse.ArgumentParser(description="한국 주식 퀀트 분석 CLI")
    parser.add_argument(
        "symbol",
        help="종목명 또는 종목 코드를 입력하세요 (예: 삼성전자 또는 005930)"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="사업보고서 기준 연도 (기본: 전년도)"
    )
    args = parser.parse_args()

    # 2) 연도 결정 (입력 없으면 현재 연도-1)
    year = args.year or datetime.datetime.now().year - 1

    # 3) 종목 정보 조회 (딕셔너리 반환)
    info = find_corp_info(args.symbol)
    corp_code = info.get("corp_code")
    corp_name = info.get("corp_name")
    if not corp_code or not corp_name:
        logger.error(f"❌ '{args.symbol}' 종목을 찾을 수 없습니다.")
        sys.exit(1)
    logger.info(f"분석 대상: {corp_name} ({corp_code}), 기준 연도: {year}")

    # 4) 데이터 수집
    data = get_combined_data(corp_code, year)
    dart_data = data.get("dart", {})
    price_df  = data.get("price", pd.DataFrame())
    pkrx_f    = data.get("pykrx", {})

    # 5) 지표 계산
    metrics = calculate_metrics(dart_data, price_df, pkrx_f)
    if not metrics:
        logger.error("⚠️ 지표 계산에 실패했습니다.")
        sys.exit(1)

    # 6) 점수 산출
    score, comment, detail = calculate_score(metrics)
    if score is None:
        logger.error("⚠️ 종합 점수 계산에 실패했습니다.")
        sys.exit(1)

    # 7) 결과 출력
    report_console(detail, score, comment)

if __name__ == "__main__":
    main()