"""
AI 음성 주식매매 챗봇 - Flask 메인 서버
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv

# 자체 모듈 임포트
from parser import parse_command, STOCK_DATABASE
from kis_api import KISApi
from database import Database
from stt_tts import clova_stt, text_to_speech

# 환경변수 로드
load_dotenv()

# Flask 앱 생성
app = Flask(__name__)
CORS(app)  # CORS 허용

# ===== 설정 =====
# Clova STT
CLOVA_CLIENT_ID = os.getenv('CLOVA_CLIENT_ID')
CLOVA_CLIENT_SECRET = os.getenv('CLOVA_CLIENT_SECRET')

# 한국투자증권 API
KIS_APP_KEY = os.getenv('KIS_APP_KEY')
KIS_APP_SECRET = os.getenv('KIS_APP_SECRET')
KIS_ACCOUNT_NO = os.getenv('KIS_ACCOUNT_NO')

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'stock_chatbot')
DB_PORT = int(os.getenv('DB_PORT', 3306))

# ===== 인스턴스 생성 =====
# 한투 API (모의투자로 시작)
kis_api = None
if KIS_APP_KEY and KIS_APP_SECRET and KIS_ACCOUNT_NO:
    try:
        kis_api = KISApi(KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT_NO, is_real=False)
        print("✅ 한국투자증권 API 초기화 완료")
    except Exception as e:
        print(f"⚠️ 한국투자증권 API 초기화 실패: {str(e)}")
        print("   API 키를 확인하거나 나중에 설정하세요.")

# Database
db = None
try:
    db = Database(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    if db.test_connection():
        print("✅ 데이터베이스 연결 완료")
except Exception as e:
    print(f"⚠️ 데이터베이스 연결 실패: {str(e)}")
    print("   MySQL 설정을 확인하거나 나중에 설정하세요.")

# 임시 사용자 ID (실제로는 로그인 시스템 필요)
TEMP_USER_ID = 1


# ===== 라우트 =====

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')


@app.route('/api/voice-to-text', methods=['POST'])
def voice_to_text():
    """음성을 텍스트로 변환 (Clova STT)"""
    try:
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({"error": "음성 파일이 없습니다"}), 400

        if not CLOVA_CLIENT_ID or not CLOVA_CLIENT_SECRET:
            return jsonify({"error": "Clova API 키가 설정되지 않았습니다"}), 500

        # Clova STT 호출
        audio_data = audio_file.read()
        text = clova_stt(audio_data, CLOVA_CLIENT_ID, CLOVA_CLIENT_SECRET)

        if text:
            # 채팅 로그 저장
            if db:
                try:
                    db.save_chat_log(TEMP_USER_ID, text, 'user')
                except:
                    pass  # DB 오류 무시

            return jsonify({
                "success": True,
                "text": text
            })
        else:
            return jsonify({
                "success": False,
                "error": "음성 인식에 실패했습니다"
            }), 400

    except Exception as e:
        print(f"❌ 음성 인식 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/process-command', methods=['POST'])
def process_command_api():
    """명령어 처리 (음성/키보드 공통)"""
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "텍스트가 없습니다"}), 400

        # 키보드 입력은 채팅 로그 저장
        if data.get('input_type') == 'keyboard' and db:
            try:
                db.save_chat_log(TEMP_USER_ID, text, 'user')
            except:
                pass

        # 명령어 파싱
        parsed = parse_command(text)

        # 응답 생성
        response = handle_command(parsed)

        # 봇 응답 저장
        if db and response.get('message'):
            try:
                db.save_chat_log(TEMP_USER_ID, response['message'], 'bot')
            except:
                pass

        return jsonify(response)

    except Exception as e:
        print(f"❌ 명령 처리 오류: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "오류가 발생했습니다. 다시 시도해주세요."
        }), 500


def handle_command(parsed: dict) -> dict:
    """파싱된 명령어 처리"""

    cmd_type = parsed.get('type')

    # API가 없는 경우 안내
    if not kis_api:
        return {
            "message": "⚠️ 한국투자증권 API가 설정되지 않았습니다.\n.env 파일에 API 키를 설정해주세요.",
            "speak": False
        }

    # 1. 조회 명령
    if cmd_type == 'query':
        query_type = parsed['query_type']

        # 현재가 조회
        if query_type == '현재가':
            stock = parsed.get('stock')
            if not stock:
                return {
                    "message": "어떤 종목의 현재가를 알려드릴까요?",
                    "speak": True
                }

            stock_code = parsed.get('stock_code')
            result = kis_api.get_current_price(stock_code)

            if result['success']:
                msg = f"""{result['stock_name']} 현재가
💰 {result['current_price']:,}원
📊 전일대비: {result['change']:+,}원 ({result['change_rate']:+.2f}%)
📈 거래량: {result['volume']:,}주"""
                return {"message": msg, "speak": True}
            else:
                return {"message": result.get('message', "현재가 조회에 실패했습니다."), "speak": True}

        # 잔고 조회
        elif query_type == '잔고':
            result = kis_api.get_balance()

            if result['success']:
                msg = f"""💰 계좌 정보
예수금: {result['deposit']:,}원
총 평가액: {result['total_value']:,}원
평가 손익: {result['profit_loss']:+,}원 ({result['profit_rate']:+.2f}%)"""
                return {"message": msg, "speak": True}
            else:
                return {"message": result.get('message', "잔고 조회에 실패했습니다."), "speak": True}

        # 보유종목 조회
        elif query_type == '보유종목':
            result = kis_api.get_holdings()

            if result['success']:
                if result['count'] == 0:
                    return {"message": "보유 중인 종목이 없습니다.", "speak": True}

                msg = f"📊 보유 종목 ({result['count']}개)\n\n"
                for i, stock in enumerate(result['holdings'], 1):
                    msg += f"{i}. {stock['stock_name']}\n"
                    msg += f"   {stock['quantity']}주 | {stock['current_price']:,}원\n"
                    msg += f"   손익: {stock['profit_loss']:+,}원 ({stock['profit_rate']:+.2f}%)\n\n"

                return {"message": msg.strip(), "speak": True}
            else:
                return {"message": result.get('message', "보유종목 조회에 실패했습니다."), "speak": True}

    # 2. 매매 명령
    elif cmd_type == 'trade':
        stock = parsed.get('stock')
        quantity = parsed.get('quantity')
        action = parsed.get('action')

        # 유효성 검증
        if not stock:
            return {"message": "어떤 종목을 거래하시겠어요?", "speak": True}

        if not quantity:
            return {"message": f"{stock} 몇 주를 {action}하시겠어요?", "speak": True}

        # 확인 요청
        price_type = parsed.get('price_type', '시장가')
        price = parsed.get('price', 0)

        # 현재가 조회 (예상금액 계산)
        stock_code = parsed.get('stock_code')
        price_info = kis_api.get_current_price(stock_code)
        estimated_price = 0

        if price_info['success']:
            if quantity == -1:  # 전량 매도
                estimated_price = 0
                quantity_text = "전량"
            else:
                estimated_price = price_info['current_price'] * quantity
                quantity_text = f"{quantity}주"
        else:
            quantity_text = f"{quantity}주" if quantity != -1 else "전량"

        confirm_msg = f"""🔔 주문 확인

종목: {stock}
수량: {quantity_text}
방식: {price_type}"""

        if estimated_price > 0:
            confirm_msg += f"\n예상금액: {estimated_price:,}원"

        confirm_msg += f"\n\n정말 {action}하시겠어요?"

        return {
            "type": "confirm",
            "message": confirm_msg,
            "speak": True,
            "confirm_data": {
                "stock": stock,
                "stock_code": stock_code,
                "quantity": quantity,
                "action": action,
                "price_type": price_type,
                "price": price
            }
        }

    # 3. 알 수 없는 명령
    else:
        return {
            "message": """무엇을 도와드릴까요?

사용 가능한 명령어:
• "삼성전자 현재가?"
• "네이버 10주 사줘"
• "카카오 전부 팔아"
• "내 잔고 확인"
• "보유 종목 보여줘"

음성 또는 키보드로 입력하세요.""",
            "speak": True
        }


@app.route('/api/execute-order', methods=['POST'])
def execute_order():
    """주문 실행"""
    try:
        if not kis_api:
            return jsonify({
                "success": False,
                "message": "한국투자증권 API가 설정되지 않았습니다."
            }), 500

        data = request.json
        confirm_data = data.get('confirm_data')

        stock_code = confirm_data['stock_code']
        quantity = confirm_data['quantity']
        action = confirm_data['action']
        price_type = confirm_data['price_type']
        price = confirm_data.get('price', 0)

        # 주문 실행
        if action == '매수':
            result = kis_api.buy_stock(stock_code, quantity, price_type, price)
        else:
            result = kis_api.sell_stock(stock_code, quantity, price_type, price)

        # DB에 저장
        if result['success'] and db:
            try:
                order_data = {
                    'stock_code': stock_code,
                    'stock_name': confirm_data['stock'],
                    'action': action,
                    'quantity': quantity,
                    'price_type': price_type,
                    'order_price': price,
                    'order_no': result.get('order_no', '')
                }
                db.save_order(TEMP_USER_ID, order_data)
            except Exception as e:
                print(f"⚠️ DB 저장 오류: {str(e)}")

        # 응답 저장
        if db and result.get('message'):
            try:
                db.save_chat_log(TEMP_USER_ID, result['message'], 'bot')
            except:
                pass

        return jsonify({
            "success": result['success'],
            "message": result['message'],
            "speak": True
        })

    except Exception as e:
        print(f"❌ 주문 실행 오류: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "주문 실행에 실패했습니다."
        }), 500


@app.route('/api/text-to-speech', methods=['POST'])
def tts_api():
    """텍스트를 음성으로 변환 (gTTS)"""
    try:
        data = request.json
        text = data.get('text', '')

        if not text:
            return jsonify({"error": "텍스트가 없습니다"}), 400

        # gTTS로 음성 생성
        audio_fp = text_to_speech(text)

        return send_file(
            audio_fp,
            mimetype='audio/mp3',
            as_attachment=False
        )

    except Exception as e:
        print(f"❌ TTS 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    status = {
        "status": "running",
        "clova_stt": bool(CLOVA_CLIENT_ID and CLOVA_CLIENT_SECRET),
        "kis_api": kis_api is not None,
        "database": db is not None and db.test_connection()
    }
    return jsonify(status)


# ===== 메인 실행 =====
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 AI 음성 주식매매 챗봇 서버 시작")
    print("=" * 70)
    print(f"📍 서버 주소: http://localhost:5000")
    print(f"🎤 Clova STT: {'✅ 활성화' if CLOVA_CLIENT_ID else '❌ 비활성화'}")
    print(f"📈 한투 API: {'✅ 활성화' if kis_api else '❌ 비활성화'}")
    print(f"🗄️  데이터베이스: {'✅ 연결됨' if db else '❌ 연결 안됨'}")
    print("=" * 70 + "\n")

    # 서버 실행
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000
    )
