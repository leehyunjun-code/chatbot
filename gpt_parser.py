"""
GPT를 사용한 주식 명령어 파싱
"""
import os
import openai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

def test_gpt_connection():
    """GPT API 연결 테스트"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "안녕하세요"}
            ],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print("GPT 응답:", result)
        print("✅ GPT API 연결 성공!")
        return True
        
    except Exception as e:
        print(f"❌ GPT API 연결 실패: {str(e)}")
        return False

def parse_stock_command(text):
    """GPT로 주식 명령어 파싱"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """
당신은 주식 거래 명령어를 분석하는 AI입니다.
사용자의 자연어 명령을 분석해서 다음 정보를 추출하세요:
- 행동: 매수, 매도, 현재가조회, 잔고조회, 보유종목조회
- 종목명: 삼성전자, SK하이닉스, 네이버, 카카오 등 (정확한 이름으로 변환)
- 수량: 숫자 (없으면 0)

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
        print(f"GPT 분석 결과:\n{result}")
        return result
        
    except Exception as e:
        print(f"GPT 파싱 오류: {str(e)}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("GPT 주식 명령어 파싱 테스트")
    print("=" * 50)
    
    # 테스트 케이스
    test_cases = [
        "삼전 10개 사줘",
        "네이버 좀 팔아",
        "카카오 얼마야?",
        "내 돈 얼마 남았어",
        "뭐 가지고 있지"
    ]
    
    for test in test_cases:
        print(f"\n입력: {test}")
        parse_stock_command(test)
        print("-" * 30)