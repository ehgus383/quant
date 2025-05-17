# data_provider.py

import os
import logging
import pandas as pd
from OpenDartReader.dart import OpenDartReader
from pykrx import stock
from config import DART_API_KEY

logger = logging.getLogger(__name__)

# DART API 인스턴스 초기화
_dart = OpenDartReader(os.getenv("DART_API_KEY", DART_API_KEY))


def get_corp_list() -> pd.DataFrame:
    """
    모든 상장/비상장 기업의 corp_code 및 corp_name을 담은 DataFrame을 반환합니다.
    """
    try:
        return _dart.corp_list()
    except Exception as e:
        logger.error(f"corp_list 조회 실패: {e}", exc_info=True)
        return pd.DataFrame()


def get_combined_data(code: str, year: int) -> dict:
    """
    DART 재무제표와 PyKrx 시세·펀더멘털을 함께 수집하여 반환합니다.

    Returns:
        {
          'dart'    : {'bs': pd.DataFrame, 'is': pd.DataFrame, 'cf': pd.DataFrame},
          'is_prev' : pd.DataFrame,            # 전년도 손익계산서 추가
          'price'   : pd.DataFrame,            # OHLCV
          'pykrx'   : dict                     # EPS, BPS, PER, PBR, DivYield, Mom12M, Volatility, FCFYield
        }
    """
    # 1) DART: 재무제표 (BS/IS/CF)
    try:
        full_df = _dart.finstate_all(code, year)
        bs  = full_df[full_df['sj_div'] == 'BS'].reset_index(drop=True)
        is_ = full_df[full_df['sj_div'] == 'IS'].reset_index(drop=True)
        cf  = full_df[full_df['sj_div'] == 'CF'].reset_index(drop=True)
        logger.info(f"[{code}-{year}] DART 재무제표 수집 완료 (BS:{len(bs)}, IS:{len(is_)}, CF:{len(cf)})")
    except Exception as e:
        logger.error(f"[{code}-{year}] DART 재무제표 수집 실패: {e}", exc_info=True)
        bs = is_ = cf = pd.DataFrame()

    # — 추가 시작 —  
    # 전년도 손익계산서(is_prev) 수집 (Revenue/NetIncome Growth 용)
    try:
        prev_full = _dart.finstate_all(code, year - 1)
        is_prev = prev_full[prev_full['sj_div'] == 'IS'].reset_index(drop=True)
    except Exception:
        is_prev = pd.DataFrame()
    # — 추가 끝 —  

    # 2) PyKrx: 일별 시세
    try:
        start = f"{year-1}0101"
        end   = f"{year}1231"
        price_df = stock.get_market_ohlcv_by_date(start, end, code)
        logger.info(f"[{code}-{year}] PyKrx 시세 수집 완료 (rows:{len(price_df)})")
    except Exception as e:
        logger.error(f"[{code}-{year}] PyKrx 시세 수집 실패: {e}", exc_info=True)
        price_df = pd.DataFrame()

    # 3) PyKrx: 펀더멘털 + 모멘텀 + 변동성 + FCFYield
    pkrx_f = {}
    if not price_df.empty:
        # 펀더멘털
        last_date = price_df.index[-1].strftime("%Y%m%d")
        try:
            fund = stock.get_market_fundamental_by_date(last_date, last_date, code).iloc[0]
            pkrx_f.update({
                'EPS':      fund['EPS'],
                'BPS':      fund['BPS'],
                'PER':      fund['PER'],
                'PBR':      fund['PBR'],
                'DivYield': fund['DIV'],
            })
        except Exception as e:
            logger.warning(f"[{code}-{year}] PyKrx 펀더멘털 조회 실패: {e}")

        # 모멘텀
        try:
            pkrx_f['Mom12M'] = price_df['종가'].iloc[-1] / price_df['종가'].iloc[0] - 1
        except Exception:
            pkrx_f['Mom12M'] = None

        # 변동성
        try:
            ret = price_df['종가'].pct_change().dropna()
            pkrx_f['Volatility'] = ret.std() * (252 ** 0.5)
        except Exception:
            pkrx_f['Volatility'] = None

        # FCFYield
        try:
            op_cf  = int(cf.loc[cf['account_nm'].str.contains('영업활동현금흐름'), 'thstrm_amount'].iloc[0])
            inv_cf = int(cf.loc[cf['account_nm'].str.contains('투자활동현금흐름'), 'thstrm_amount'].iloc[0])
            mcap   = stock.get_market_cap_by_date(last_date, last_date, code).iloc[0]['시가총액']
            pkrx_f['FCFYield'] = (op_cf + inv_cf) / mcap if mcap else None
        except Exception:
            pkrx_f['FCFYield'] = None

    return {
        'dart':    {'bs': bs, 'is': is_, 'cf': cf},
        'is_prev': is_prev,   # 전년도 IS 추가
        'price':   price_df,
        'pykrx':   pkrx_f,
    }