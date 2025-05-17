# test_scorer.py

from data_provider import get_combined_data
from metrics import calculate_metrics
from scorer import calculate_score

if __name__ == "__main__":
    # 삼성전자(005930), 기준 연도 2023
    code, year = "005930", 2023

    # 1) 데이터 수집
    data = get_combined_data(code, year)

    # 2) 지표 계산
    metrics = calculate_metrics(data, data["price"], data["pykrx"])

    # 3) 점수 계산
    composite_score, comment, details = calculate_score(metrics)

    # 4) 결과 출력
    print(f"=== {code} ({year}) 퀀트 점수 ===")
    print(f"Composite Score : {composite_score:.2f}")
    print(f"Comment         : {comment}")
    print("Detail Scores   :")
    for k, v in details.items():
        print(f" - {k:20s}: {v:.2f}")