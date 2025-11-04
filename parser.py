"""
명령어 파싱 엔진
사용자의 음성/텍스트 입력을 분석하여 매매/조회 명령을 추출합니다.
GPT-3.5를 우선 사용하고, 실패시 기존 규칙 기반 파서를 사용합니다.
"""

from typing import Optional, Dict
import re
import difflib
import openai
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')


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


# ===== 2. GPT 파싱 함수 =====
def parse_with_gpt(text: str) -> Dict:
    """GPT를 사용한 명령어 파싱 (실패시 기존 파서 사용)"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
당신은 주식 거래 명령어를 분석하는 AI입니다.
사용자의 자연어 명령을 분석해서 다음 정보를 추출하세요:
- 행동: 매수, 매도, 현재가, 잔고, 보유종목
- 종목명: 삼성전자, SK하이닉스, 네이버, 카카오 등 (정확한 이름으로 변환)
- 수량: 숫자 (없으면 1)

응답 형식:
행동: [매수/매도/현재가/잔고/보유종목]
종목: [종목명]
수량: [숫자]
"""},
                {"role": "user", "content": text}
            ],
            max_tokens=100,
            temperature=0.3
        )
        
        result = response.choices[0].message.content
        print(f"GPT 분석: {result}")  # 디버깅용
        
        # GPT 응답을 파싱
        lines = result.strip().split('\n')
        action = None
        stock = None
        quantity = 1
        
        for line in lines:
            if '행동:' in line:
                action = line.split(':')[1].strip()
            elif '종목:' in line:
                stock_name = line.split(':')[1].strip()
                if stock_name != '없음':
                    stock = stock_name
            elif '수량:' in line:
                qty = line.split(':')[1].strip()
                if qty.isdigit():
                    quantity = int(qty)
        
        # 기존 형식으로 변환
        if action in ['매수', '매도']:
            return {
                'type': 'trade',
                'action': action,
                'stock': stock,
                'stock_code': STOCK_DATABASE.get(stock) if stock else None,
                'quantity': quantity if quantity > 0 else 1,
                'price_type': '시장가',
                'raw_text': text
            }
        elif action in ['현재가', '현재가조회']:
            return {
                'type': 'query',
                'query_type': '현재가',
                'stock': stock,
                'stock_code': STOCK_DATABASE.get(stock) if stock else None,
                'raw_text': text
            }
        elif action in ['잔고', '잔고조회']:
            return {'type': 'query', 'query_type': '잔고', 'raw_text': text}
        elif action in ['보유종목', '보유종목조회']:
            return {'type': 'query', 'query_type': '보유종목', 'raw_text': text}
    
    except Exception as e:
        print(f"GPT 파싱 실패, 기존 파서 사용: {str(e)}")
    
    # GPT 실패시 기존 파서 사용
    return parse_command_original(text)


# ===== 3. 기존 파싱 엔진 (백업용) =====

# 키워드 정의
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

# 한글 숫자 변환
KOREAN_NUMBER_MAP = {
    '영': 0, '공': 0, '일': 1, '이': 2, '삼': 3,
    '사': 4, '오': 5, '육': 6, '륙': 6, '칠': 7,
    '팔': 8, '구': 9, '십': 10, '백': 100,
    '천': 1000, '만': 10000
}


def korean_to_number(text: str) -> int:
    """한글 숫자를 아라비아 숫자로 변환"""
    text = text.strip()
    
    if text.isdigit():
        return int(text)
    
    total = 0
    current = 0
    
    for char in text:
        if char in KOREAN_NUMBER_MAP:
            value = KOREAN_NUMBER_MAP[char]
            
            if value >= 10:
                if current == 0:
                    current = 1
                current *= value
                total += current
                current = 0
            else:
                current += value
    
    total += current
    return total


def detect_action(text: str) -> Optional[str]:
    """매수/매도 행동 감지"""
    text_lower = text.lower()
    
    for keyword in BUY_KEYWORDS:
        if keyword in text_lower:
            return "매수"
    
    for keyword in SELL_KEYWORDS:
        if keyword in text_lower:
            return "매도"
    
    return None


def detect_query_type(text: str) -> Optional[str]:
    """조회 유형 감지"""
    text_lower = text.lower()
    
    for keyword in PRICE_KEYWORDS:
        if keyword in text_lower:
            return "현재가"
    
    for keyword in BALANCE_KEYWORDS:
        if keyword in text_lower:
            return "잔고"
    
    for keyword in HOLDINGS_KEYWORDS:
        if keyword in text_lower:
            return "보유종목"
    
    return None


def match_stock(text: str) -> Optional[str]:
    """종목명 찾기 (오타 자동 수정)"""
    stock_names = list(STOCK_DATABASE.keys())
    
    # 정확히 일치하는 종목 우선
    for stock in stock_names:
        if stock in text:
            return stock
    
    # Fuzzy Matching
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


def extract_quantity(text: str) -> Optional[int]:
    """주식 수량 추출"""
    # 아라비아 숫자 + "주"
    match = re.search(r'(\d+)\s*주', text)
    if match:
        return int(match.group(1))
    
    # 한글 숫자 + "주"
    match = re.search(r'([가-힣]+)\s*주', text)
    if match:
        korean_num = match.group(1)
        try:
            num = korean_to_number(korean_num)
            if num > 0:
                return num
        except:
            pass
    
    # "전부", "전량", "모두"
    if any(word in text for word in ['전부', '전량', '모두', '다']):
        return -1
    
    return None


def extract_price_type(text: str) -> tuple:
    """주문 방식 판단 (시장가/지정가)"""
    if '시장가' in text:
        return ("시장가", 0)
    
    match = re.search(r'지정가\s*(\d+)', text)
    if match:
        price = int(match.group(1))
        return ("지정가", price)
    
    match = re.search(r'(\d{4,})\s*원', text)
    if match:
        price = int(match.group(1))
        return ("지정가", price)
    
    return ("시장가", 0)


def parse_command_original(text: str) -> Dict:
    """기존 규칙 기반 명령어 파싱"""
    text = text.strip()
    result = {"raw_text": text}
    
    # 1. 조회 명령인지 확인
    query_type = detect_query_type(text)
    if query_type:
        result["type"] = "query"
        result["query_type"] = query_type
        
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
        
        stock = match_stock(text)
        if stock:
            result["stock"] = stock
            result["stock_code"] = STOCK_DATABASE[stock]
        
        quantity = extract_quantity(text)
        if quantity:
            result["quantity"] = quantity
        
        price_type, price = extract_price_type(text)
        result["price_type"] = price_type
        result["price"] = price
        
        return result
    
    # 3. 알 수 없는 명령
    result["type"] = "unknown"
    return result


# ===== 4. 메인 파싱 함수 =====
def parse_command(text: str) -> Dict:
    """메인 파싱 함수 - GPT 우선, 실패시 기존 파서"""
    if openai.api_key:
        return parse_with_gpt(text)
    else:
        return parse_command_original(text)


# ===== 5. 테스트 함수 =====
def test_parser():
    """파싱 엔진 테스트"""
    test_cases = [
        "삼성전자 10주 사줘",
        "삼전 5개 사자",
        "네이버 좀 팔아",
        "카카오 얼마야?",
        "내 잔고 확인",
        "뭐 가지고 있지",
        "현대차 전부 팔아",
    ]
    
    print("=" * 70)
    print("명령어 파싱 엔진 테스트 (GPT 통합)")
    print("=" * 70)
    
    for i, test in enumerate(test_cases, 1):
        result = parse_command(test)
        print(f"\n[테스트 {i}]")
        print(f"입력: {test}")
        print(f"결과: {result}")
        print("-" * 70)


if __name__ == "__main__":
    test_parser()