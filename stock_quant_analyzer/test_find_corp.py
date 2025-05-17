# utils.py

import os
import logging
from OpenDartReader.dart import OpenDartReader
from config import DART_API_KEY

logger = logging.getLogger(__name__)
_dart = OpenDartReader(os.getenv("DART_API_KEY", DART_API_KEY))

def find_corp_info(query: str) -> dict:
    """
    종목명 또는 종목코드(6자리)로 DART 기업 고유번호(corp_code)와
    공식 기업명(corp_name)을 조회하여 딕셔너리로 반환합니다.
    실패 시 {'corp_code': None, 'corp_name': None} 반환.
    """
    query = query.strip()
    corp_code = None
    corp_name = None

    # 1) 종목코드(6자리)로 시도
    if query.isdigit() and len(query) == 6:
        try:
            corp_code = _dart.find_corp_code(query)
            info = _dart.company(corp_code)
            if isinstance(info, dict):
                corp_name = info.get("corp_name")
            else:
                corp_name = info.loc[0, "corp_name"]
            return {"corp_code": corp_code, "corp_name": corp_name}
        except Exception as e:
            logger.warning(f"find_corp_code 실패 for {query}: {e}")

    # 2) 기업명으로 시도
    try:
        corp_code = _dart.find_corp_code(query)
        info = _dart.company(corp_code)
        if isinstance(info, dict):
            corp_name = info.get("corp_name")
        else:
            corp_name = info.loc[0, "corp_name"]
        return {"corp_code": corp_code, "corp_name": corp_name}
    except Exception as e:
        logger.warning(f"find_corp_info by find_corp_code failed for '{query}': {e}")

    # 3) company_by_name으로 최종 시도
    try:
        df = _dart.company_by_name(query)
        if not df.empty:
            row = df.iloc[0]
            return {"corp_code": row["corp_code"], "corp_name": row["corp_name"]}
    except Exception as e:
        logger.error(f"company_by_name 실패 for '{query}': {e}", exc_info=True)

    # 실패 시
    return {"corp_code": None, "corp_name": None}