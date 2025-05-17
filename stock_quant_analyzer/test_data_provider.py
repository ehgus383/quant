# test_data_provider.py

from data_provider import get_combined_data

if __name__ == "__main__":
    code, year = "005930", 2023  # 삼성전자, 예시 연도
    data = get_combined_data(code, year)
    print("▶ DART BS rows:", len(data['dart']['bs']))
    print("▶ DART IS rows:", len(data['dart']['is']))
    print("▶ DART CF rows:", len(data['dart']['cf']))
    print("▶ Price rows:", len(data['price']))
    print("▶ PyKrx keys:", list(data['pykrx'].keys()))