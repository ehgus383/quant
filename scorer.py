# scorer.py

import numpy as np
import logging
from typing import Dict, Optional, Tuple
from config import SCORING_WEIGHTS, SCORE_COMMENTS, METRIC_TARGETS

logger = logging.getLogger(__name__)


def normalize_min_max(value: Optional[float], good_value: float, bad_value: float, direction: str = 'high') -> float:
    """
    Min-Max 정규화를 사용하여 지표 값을 0~1 사이로 변환합니다.
    None 값은 최저 점수인 0.0으로 처리합니다.
    """
    if value is None:
        logger.debug("정규화 입력값이 None이므로 0.0점 부여.")
        return 0.0

    min_val, max_val = (bad_value, good_value) if direction == 'high' else (good_value, bad_value)
    if max_val == min_val:
        logger.warning(f"정규화 good({good_value}), bad({bad_value}) 값이 동일합니다. 0.5점 부여.")
        return 0.5

    # 클리핑
    if (direction == 'high' and value >= max_val) or (direction == 'low' and value <= min_val):
        return 1.0
    if (direction == 'high' and value <= min_val) or (direction == 'low' and value >= max_val):
        return 0.0

    try:
        normalized = (value - min_val) / (max_val - min_val)
        return normalized if direction == 'high' else 1.0 - normalized
    except ZeroDivisionError:
        logger.error("정규화 중 ZeroDivisionError 발생", exc_info=True)
        return 0.5


def calculate_score(metrics: Dict[str, Optional[float]]) -> Optional[Tuple[Optional[float], str, Dict[str, float]]]:
    """
    지표 딕셔너리를 받아 종합 점수(0~100), 코멘트, 개별 0~100 점수를 반환합니다.
    성장 지표(RevenueGrowth, NetIncomeGrowth)가 None 또는 음수인 경우 스코어링에서 제외됩니다.
    """
    if not metrics:
        logger.error("점수 계산 불가: 입력된 지표 데이터 없음.")
        return None

    total_score = 0.0
    total_weight = 0.0
    scores_detail: Dict[str, float] = {}

    logger.info("--- 퀀트 점수 계산 시작 ---")

    for metric_name, weight in SCORING_WEIGHTS.items():
        # 성장 지표 음수/None 제외
        if metric_name in ("RevenueGrowth", "NetIncomeGrowth"):
            val = metrics.get(metric_name)
            if val is None or val < 0:
                logger.info(f"{metric_name}: 값({val})이 None 또는 음수이므로 스코어링 제외")
                continue

        if metric_name in metrics and metric_name in METRIC_TARGETS:
            value = metrics[metric_name]
            target = METRIC_TARGETS[metric_name]

            normalized = normalize_min_max(
                value,
                target["good"],
                target["bad"],
                target["direction"]
            )
            metric_score = normalized * weight
            total_score += metric_score
            total_weight += weight
            scores_detail[metric_name] = normalized * 100

            value_str = f"{value:.2f}" if isinstance(value, (int, float)) else "N/A"
            logger.debug(
                f"점수 계산: {metric_name} (값:{value_str}) -> "
                f"정규화:{normalized:.2f} -> 가중점수:{metric_score:.2f} (가중치:{weight})"
            )
        else:
            logger.warning(f"스코어링 대상 '{metric_name}' 지표 누락 또는 설정 없음, 제외")

    if total_weight > 0:
        composite = (total_score / total_weight) * 100
        composite = max(0.0, min(100.0, composite))
        logger.info(f"총 가중치 합계: {total_weight:.2f}, 종합 점수(0-100): {composite:.2f}")
    else:
        logger.error("유효 가중치 합계가 0, 종합 점수 계산 불가")
        composite = None

    comment = "평가 불가"
    if composite is not None:
        for (low, high), msg in sorted(SCORE_COMMENTS.items(), reverse=True):
            if low <= composite < high:
                comment = msg
                break

    logger.info(f"최종 평가: {comment}")
    logger.info("--- 퀀트 점수 계산 완료 ---")

    return composite, comment, scores_detail