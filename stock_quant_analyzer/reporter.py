# reporter.py

from tabulate import tabulate
from colorama import init, Fore, Style
from typing import Dict

# 컬러 출력 초기화
init(autoreset=True)

def report_console(metrics: Dict[str, float], score: float, comment: str) -> None:
    """
    콘솔에 지표별 점수와 종합 점수를 컬러로 강조하여 출력합니다.
    - metrics: 지표별 0~100 스케일 점수 딕셔너리
    - score: 종합 점수 (0~100)
    - comment: SCORE_COMMENTS에 따른 평가 문자열
    """
    # 헤더
    print(Fore.CYAN + Style.BRIGHT + f"\n=== 종합 점수: {score:.1f}점 — {comment} ===\n")

    # 지표별 테이블 준비 (이름, 0~100 점수)
    table = [(name, f"{value:.1f}") for name, value in metrics.items()]
    print(tabulate(table, headers=["지표", "점수"], tablefmt="github"))

    print()  # 한 줄 띄우기