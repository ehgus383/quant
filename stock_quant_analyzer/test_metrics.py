# test_metrics.py

from data_provider import get_combined_data
from metrics import calculate_metrics

if __name__ == "__main__":
    code, year = "005930", 2023          # 삼성전자, 기준 연도

    # 번들 전체 수집 (dart + is_prev + price + pykrx)
    data = get_combined_data(code, year)

    # ★ calculate_metrics 에 'data' 전체를 그대로 넘깁니다 ★
    metrics = calculate_metrics(data, data["price"], data["pykrx"])

    print(f"=== {code} ({year}) 지표 계산 결과 ===")
    for k, v in metrics.items():
        print(f"{k:20s}: {v}")