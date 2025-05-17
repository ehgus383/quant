# config.py

# 1) DART API 키 설정 (발급받은 키를 입력해주세요)
DART_API_KEY = "794a2fa036677b8146849f039bd7f8ec985096d6"

# 2) 팩터 가중치 (핵심: 성장 비중을 절반으로 낮춤)
SCORING_WEIGHTS = {
    # 펀더멘털
    'ROE':             0.12,  # 자기자본이익률
    'OperatingMargin': 0.08,  # 영업이익률
    'ROA':             0.05,  # 총자산이익률
    'DebtRatio':       0.08,  # 부채비율
    'CurrentRatio':    0.04,  # 유동비율

    # 성장 (종전 0.08 → 0.04로 축소)
    'RevenueGrowth':   0.04,  # 매출증가율
    'NetIncomeGrowth': 0.04,  # 순이익증가율

    # 밸류
    'PER':             0.08,  # 주가수익비율
    'PBR':             0.04,  # 주가순자산비율
    'DivYield':        0.10,  # 배당수익률

    # 모멘텀/리스크
    'Mom12M':          0.12,  # 12개월 모멘텀
    'Volatility':      0.05,  # 연간 변동성
    'FCFYield':        0.08,  # 잉여현금흐름 수익률
}

# 3) 정규화 목표값 (good=최고, bad=최저, direction='high' or 'low')
METRIC_TARGETS = {
    # 펀더멘털
    'ROE':             {'good':15,   'bad':0,    'direction':'high'},
    'OperatingMargin': {'good':10,   'bad':0,    'direction':'high'},
    'ROA':             {'good':10,   'bad':0,    'direction':'high'},
    'DebtRatio':       {'good':100,  'bad':300,  'direction':'low'},
    'CurrentRatio':    {'good':150,  'bad':100,  'direction':'high'},
    # 성장
    'RevenueGrowth':   {'good':10,   'bad':-10,  'direction':'high'},
    'NetIncomeGrowth': {'good':10,   'bad':-10,  'direction':'high'},
    # 밸류
    'PER':             {'good':8,    'bad':20,   'direction':'low'},
    'PBR':             {'good':1,    'bad':3,    'direction':'low'},
    'DivYield':        {'good':4,    'bad':0,    'direction':'high'},
    # 모멘텀/리스크
    'Mom12M':          {'good':0.20, 'bad':-0.20,'direction':'high'},
    'Volatility':      {'good':0.20, 'bad':0.40, 'direction':'low'},
    'FCFYield':        {'good':0.08, 'bad':0.00, 'direction':'high'},
}

# 4) 점수 구간별 코멘트
SCORE_COMMENTS = {
    (90, 101): "최상급 - 매우 우수한 퀀트 스코어",
    (70, 90):  "우수 - 투자매력 높음",
    (50, 70):  "보통 - 시장 평균 수준",
    (0, 50):   "주의 - 추가 분석 필요",
}