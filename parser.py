"""
명령어 파싱 엔진
사용자의 음성/텍스트 입력을 분석하여 매매/조회 명령을 추출합니다.
"""

from typing import Optional, Dict
import re
import difflib


# ===== 1. 종목 데이터베이스 =====
STOCK_DATABASE = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "네이버": "035420",
    "카카오": "035720",
    "현대자동차": "005380",
    "LG전자": "066570",
    "삼성바이오로직스": "207940",
    "POSCO홀딩스": "005490",
    "LG화학": "051910",
    "기아": "000270",
    "삼성SDI": "006400",
    "셀트리온": "068270",
    "SK이노베이션": "096770",
    "KB금융": "105560",
    "신한지주": "055550",
    "하나금융지주": "086790",
    "NAVER": "035420",
    "삼성물산": "028260",
    "LG생활건강": "051900",
    "삼성생명": "032830",
    "한국전력": "015760",
    "포스코": "005490",
    "현대모비스": "012330",
    "SK텔레콤": "017670",
    "KT": "030200",
    "LG유플러스": "032640",
    "엔씨소프트": "036570",
    "넷마블": "251270",
    "크래프톤": "259960",
    "카카오뱅크": "323410",
    "카카오페이": "377300",
}


# ===== 2. 키워드 정의 =====
BUY_KEYWORDS = [
    '사', '사줘', '사주세요', '매수', '매수해', '매수해줘',
    '매수해주세요', '구매', '구매해', '구매해줘', '살게', '사자',
    '매입', '매입해', '매입해줘'
]

SELL_KEYWORDS = [
    '팔', '팔아', '팔아줘', '팔아주세요', '매도', '매도해',
    '매도해줘', '매도해주세요', '판매', '판매해', '판매해줘',
    '팔게', '팔자', '처분', '처분해'
]

PRICE_KEYWORDS = [
    '현재가', '가격', '시세', '얼마', '호가', '가격표',
    '지금', '현재', '값', '시가'
]

BALANCE_KEYWORDS = [
    '잔고', '얼마남았', '돈', '예수금', '내돈', '잔액',
    '남은돈', '내계좌', '계좌', '돈얼마'
]

HOLDINGS_KEYWORDS = [
    '보유', '가진', '내주식', '내꺼', '포트폴리오', '보유종목',
    '내가가진', '내것', '보유주식', '내종목'
]


# ===== 3. 한글 숫자 변환 =====
KOREAN_NUMBER_MAP = {
    '영': 0, '공': 0, '일': 1, '이': 2, '삼': 3,
    '사': 4, '오': 5, '육': 6, '륙': 6, '칠': 7,
    '팔': 8, '구': 9, '십': 10, '백': 100,
    '천': 1000, '만': 10000
}


def korean_to_number(text: str) -> int:
    """한글 숫자를 아라비아 숫자로 변환

    Args:
        text: 한글 숫자 문자열 (예: "십오", "육십")

    Returns:
        int: 변환된 숫자

    Examples:
        >>> korean_to_number("십오")
        15
        >>> korean_to_number("육십")
        60
    """
    text = text.strip()

    # 이미 숫자인 경우
    if text.isdigit():
        return int(text)

    total = 0
    current = 0

    for char in text:
        if char in KOREAN_NUMBER_MAP:
            value = KOREAN_NUMBER_MAP[char]

            if value >= 10:  # 단위 (십, 백, 천, 만)
                if current == 0:
                    current = 1
                current *= value
                total += current
                current = 0
            else:  # 숫자 (일, 이, 삼...)
                current += value

    total += current
    return total


# ===== 4. 행동 판단 =====
def detect_action(text: str) -> Optional[str]:
    """매수/매도 행동 감지

    Args:
        text: 사용자 입력 텍스트

    Returns:
        str: "매수" 또는 "매도", 없으면 None
    """
    text_lower = text.lower()

    # 매수 키워드 확인
    for keyword in BUY_KEYWORDS:
        if keyword in text_lower:
            return "매수"

    # 매도 키워드 확인
    for keyword in SELL_KEYWORDS:
        if keyword in text_lower:
            return "매도"

    return None


def detect_query_type(text: str) -> Optional[str]:
    """조회 유형 감지

    Args:
        text: 사용자 입력 텍스트

    Returns:
        str: "현재가", "잔고", "보유종목" 중 하나, 없으면 None
    """
    text_lower = text.lower()

    # 현재가 조회
    for keyword in PRICE_KEYWORDS:
        if keyword in text_lower:
            return "현재가"

    # 잔고 조회
    for keyword in BALANCE_KEYWORDS:
        if keyword in text_lower:
            return "잔고"

    # 보유종목 조회
    for keyword in HOLDINGS_KEYWORDS:
        if keyword in text_lower:
            return "보유종목"

    return None


# ===== 5. 종목명 매칭 (Fuzzy Matching) =====
def match_stock(text: str) -> Optional[str]:
    """종목명 찾기 (오타 자동 수정)

    Args:
        text: 사용자 입력 텍스트

    Returns:
        str: 매칭된 종목명, 없으면 None

    Examples:
        >>> match_stock("삼성전자 10주 사줘")
        "삼성전자"
        >>> match_stock("삼송전자")  # 오타
        "삼성전자"
    """
    stock_names = list(STOCK_DATABASE.keys())

    # 1. 정확히 일치하는 종목 우선
    for stock in stock_names:
        if stock in text:
            return stock

    # 2. Fuzzy Matching (유사도 60% 이상)
    words = re.findall(r'[가-힣A-Za-z0-9]+', text)
    for word in words:
        matches = difflib.get_close_matches(
            word,
            stock_names,
            n=1,
            cutoff=0.6
        )
        if matches:
            return matches[0]

    return None


# ===== 6. 수량 추출 =====
def extract_quantity(text: str) -> Optional[int]:
    """주식 수량 추출

    Args:
        text: 사용자 입력 텍스트

    Returns:
        int: 수량 (전부인 경우 -1), 없으면 None

    Examples:
        >>> extract_quantity("10주 사줘")
        10
        >>> extract_quantity("육주 팔아")
        6
        >>> extract_quantity("전부 매도")
        -1
    """
    # 1. 아라비아 숫자 + "주"
    match = re.search(r'(\d+)\s*주', text)
    if match:
        return int(match.group(1))

    # 2. 한글 숫자 + "주"
    match = re.search(r'([가-힣]+)\s*주', text)
    if match:
        korean_num = match.group(1)
        try:
            num = korean_to_number(korean_num)
            if num > 0:
                return num
        except:
            pass

    # 3. "전부", "전량", "모두" → 특수 케이스
    if any(word in text for word in ['전부', '전량', '모두', '다', '올인', '올인']):
        return -1

    return None


# ===== 7. 가격 및 주문 방식 =====
def extract_price_type(text: str) -> tuple:
    """주문 방식 판단 (시장가/지정가)

    Args:
        text: 사용자 입력 텍스트

    Returns:
        tuple: (주문방식, 가격)
        예: ("시장가", 0) 또는 ("지정가", 75000)
    """
    # 1. 시장가 명시
    if '시장가' in text:
        return ("시장가", 0)

    # 2. 지정가 명시 + 가격
    match = re.search(r'지정가\s*(\d+)', text)
    if match:
        price = int(match.group(1))
        return ("지정가", price)

    # 3. 특정 가격만 언급
    match = re.search(r'(\d{4,})\s*원', text)
    if match:
        price = int(match.group(1))
        return ("지정가", price)

    # 4. 기본값: 시장가
    return ("시장가", 0)


# ===== 8. 메인 파싱 함수 =====
def parse_command(text: str) -> Dict:
    """명령어 파싱 메인 함수

    사용자 입력을 분석하여 구조화된 데이터로 변환합니다.

    Args:
        text: 사용자 입력 텍스트

    Returns:
        dict: 파싱된 명령어 정보
        {
            "type": "trade" | "query" | "unknown",
            "action": "매수" | "매도",
            "query_type": "현재가" | "잔고" | "보유종목",
            "stock": "삼성전자",
            "stock_code": "005930",
            "quantity": 10,
            "price_type": "시장가",
            "price": 0,
            "raw_text": "원본 텍스트"
        }

    Examples:
        >>> parse_command("삼성전자 10주 사줘")
        {'type': 'trade', 'action': '매수', 'stock': '삼성전자', ...}

        >>> parse_command("네이버 현재가?")
        {'type': 'query', 'query_type': '현재가', 'stock': '네이버', ...}
    """
    text = text.strip()
    result = {"raw_text": text}

    # 1. 조회 명령인지 확인
    query_type = detect_query_type(text)
    if query_type:
        result["type"] = "query"
        result["query_type"] = query_type

        # 현재가 조회는 종목명 필요
        if query_type == "현재가":
            stock = match_stock(text)
            if stock:
                result["stock"] = stock
                result["stock_code"] = STOCK_DATABASE[stock]

        return result

    # 2. 매매 명령인지 확인
    action = detect_action(text)
    if action:
        result["type"] = "trade"
        result["action"] = action

        # 종목 찾기
        stock = match_stock(text)
        if stock:
            result["stock"] = stock
            result["stock_code"] = STOCK_DATABASE[stock]

        # 수량 찾기
        quantity = extract_quantity(text)
        if quantity:
            result["quantity"] = quantity

        # 가격 방식 및 가격
        price_type, price = extract_price_type(text)
        result["price_type"] = price_type
        result["price"] = price

        return result

    # 3. 알 수 없는 명령
    result["type"] = "unknown"
    return result


# ===== 9. 테스트 함수 =====
def test_parser():
    """파싱 엔진 테스트"""
    test_cases = [
        "삼성전자 10주 사줘",
        "네이버 육주 팔아",
        "카카오 현재가 알려줘",
        "내 잔고 확인",
        "보유 종목 보여줘",
        "삼송전자 5주 매수",  # 오타 테스트
        "현대차 전부 팔아",
        "LG전자 20주 지정가 85000원 매수",
        "SK하이닉스 시장가로 15주 구매",
        "셀트리온 얼마야?",
    ]

    print("=" * 70)
    print("명령어 파싱 엔진 테스트")
    print("=" * 70)

    for i, test in enumerate(test_cases, 1):
        result = parse_command(test)
        print(f"\n[테스트 {i}]")
        print(f"입력: {test}")
        print(f"결과: {result}")
        print("-" * 70)


if __name__ == "__main__":
    # 테스트 실행
    test_parser()
