# metrics.py

import re
import pandas as pd
import numpy as np
from typing import Dict, Optional
from config import METRIC_TARGETS, DART_API_KEY
from OpenDartReader.dart import OpenDartReader

# ------------------------------------------------------------------ #
# 1. 계정명 Alias 정의
# ------------------------------------------------------------------ #
ALIASES = {
    "operating_income": {
        "ids": [
            "ifrs-full_ProfitLossFromOperatingActivities",
            "ifrs-full_OperatingIncomeLoss",
        ],
        "names": [
            "영업이익", "영업이익(손실)", "영업이익(또는손실)",
            "operating income", "operating income(loss)"
        ],
    },
    "revenue": {
        "ids": [
            "ifrs-full_Revenue",
            "ifrs-full_SalesRevenueGoods",
        ],
        "names": ["매출액", "sales revenue", "revenue"],
    },
    "net_income": {
        "ids": ["ifrs-full_ProfitLoss"],
        "names": ["당기순이익", "net income", "profit(loss)"],
    },
    "total_assets": {"names": ["자산총계", "total assets"]},
    "equity": {"names": ["자본총계", "total equity"]},
    "total_liabilities": {"names": ["부채총계", "total liabilities"]},
    "current_assets": {"names": ["유동자산", "current assets"]},
    "current_liabilities": {"names": ["유동부채", "current liabilities"]},
    "op_cf": {"names": ["영업활동현금흐름", "net cash from operating activities"]},
    "inv_cf": {"names": ["투자활동현금흐름", "net cash used in investing activities"]},
}

# ------------------------------------------------------------------ #
def normalize(name: str) -> str:
    """영문/한글 계정명을 비교하기 전에 전처리(공백·괄호·Zero width 제거)."""
    return re.sub(r"[\s()\u200b]", "", name).lower()

def _lookup(df: pd.DataFrame, aliases: Dict[str, list]) -> Optional[float]:
    """
    1) account_id 우선
    2) account_nm normalize 후 exact 매칭
    3) account_nm normalize 후 contains 부분 매칭
    """
    if df is None or df.empty:
        return None

    # 1) account_id 매칭
    if "account_id" in df.columns and aliases.get("ids"):
        hit = df[df["account_id"].isin(aliases["ids"])]
        if not hit.empty:
            return pd.to_numeric(hit["thstrm_amount"], errors="coerce").iloc[0]

    # 2) account_nm exact
    if aliases.get("names"):
        targets = [normalize(x) for x in aliases["names"]]
        df["__nm__"] = df["account_nm"].map(normalize)
        exact = df[df["__nm__"].isin(targets)]
        if not exact.empty:
            return pd.to_numeric(exact["thstrm_amount"], errors="coerce").iloc[0]

        # 3) contains fallback
        pattern = "|".join(targets)
        contains = df[df["__nm__"].str.contains(pattern, na=False)]
        if not contains.empty:
            return pd.to_numeric(contains["thstrm_amount"], errors="coerce").iloc[0]

    return None

# ------------------------------------------------------------------ #
def calculate_metrics(
    dart_data: Dict[str, pd.DataFrame],
    price_df: pd.DataFrame,
    pkrx_f: Dict[str, float],
) -> Dict[str, Optional[float]]:
    """
    DART + PyKrx 원시 데이터를 받아 주요 퀀트 지표를 계산해 반환합니다.
    dart_data 딕셔너리에 'is_prev'(전년도 IS)가 없으면 자동으로 불러옵니다.
    """

    # 기본 데이터
    bs   = dart_data.get("bs", pd.DataFrame())
    is_  = dart_data.get("is", pd.DataFrame())
    cf   = dart_data.get("cf", pd.DataFrame())
    is_prev = dart_data.get("is_prev", pd.DataFrame())

    # -- 전년도 IS 자동 로드 (is_prev 없을 때) --
    if is_prev.empty and not is_.empty:
        try:
            corp_code = is_["corp_code"].iloc[0]
            year = int(is_["bsns_year"].iloc[0])
            reader = OpenDartReader(DART_API_KEY)
            prev_full = reader.finstate_all(corp_code, year - 1)
            is_prev = prev_full[prev_full["sj_div"] == "IS"].reset_index(drop=True)
        except Exception:
            is_prev = pd.DataFrame()

    metrics: Dict[str, Optional[float]] = {}

    # ---------------- 펀더멘털 ---------------- #
    net_inc  = _lookup(is_,   ALIASES["net_income"])
    equity   = _lookup(bs,    ALIASES["equity"])
    op_inc   = _lookup(is_,   ALIASES["operating_income"])
    revenue  = _lookup(is_,   ALIASES["revenue"])
    t_assets = _lookup(bs,    ALIASES["total_assets"])
    t_liab   = _lookup(bs,    ALIASES["total_liabilities"])
    c_assets = _lookup(bs,    ALIASES["current_assets"])
    c_liab   = _lookup(bs,    ALIASES["current_liabilities"])

    metrics["ROE"]             = (net_inc / equity   * 100) if net_inc and equity else None
    metrics["OperatingMargin"] = (op_inc / revenue   * 100) if op_inc and revenue else None
    metrics["ROA"]             = (net_inc / t_assets * 100) if net_inc and t_assets else None
    metrics["DebtRatio"]       = (t_liab / equity    * 100) if t_liab and equity else None
    metrics["CurrentRatio"]    = (c_assets / c_liab  * 100) if c_assets and c_liab else None

    # ---------------- 성장 지표 ---------------- #
    prev_rev = _lookup(is_prev, ALIASES["revenue"])
    prev_inc = _lookup(is_prev, ALIASES["net_income"])
    metrics["RevenueGrowth"] = (
        (revenue - prev_rev) / prev_rev * 100
        if revenue is not None and prev_rev not in (None, 0) else None
    )
    metrics["NetIncomeGrowth"] = (
        (net_inc - prev_inc) / prev_inc * 100
        if net_inc is not None and prev_inc not in (None, 0) else None
    )

    # ---------------- 밸류 지표 ---------------- #
    metrics["PER"]      = pkrx_f.get("PER")
    metrics["PBR"]      = pkrx_f.get("PBR")
    metrics["DivYield"] = pkrx_f.get("DivYield")

    # --------- 모멘텀 / 변동성 ------------- #
    try:
        metrics["Mom12M"] = price_df["종가"].iloc[-1] / price_df["종가"].iloc[0] - 1
    except Exception:
        metrics["Mom12M"] = None
    try:
        ret = price_df["종가"].pct_change().dropna()
        metrics["Volatility"] = ret.std() * np.sqrt(252)
    except Exception:
        metrics["Volatility"] = None

    # --------- FCF 수익률 ------------------ #
    op_cf  = _lookup(cf,      ALIASES["op_cf"])
    inv_cf = _lookup(cf,      ALIASES["inv_cf"])
    mcap   = pkrx_f.get("MarketCap")
    if mcap is None and equity and pkrx_f.get("BPS") and not price_df.empty:
        shares = equity / pkrx_f["BPS"]
        mcap   = shares * price_df["종가"].iloc[-1]
    metrics["FCFYield"] = (
        (op_cf + inv_cf) / mcap
        if op_cf and inv_cf and mcap is not None else None
    )

    return metrics