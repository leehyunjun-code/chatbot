"""
음성 인식 및 음성 합성 모듈
- Clova STT: 음성 → 텍스트
- gTTS: 텍스트 → 음성
"""

import requests
from gtts import gTTS
import io
from typing import Optional


def clova_stt(audio_data: bytes, client_id: str, client_secret: str,
              lang: str = "Kor") -> Optional[str]:
    """Clova STT API를 사용하여 음성을 텍스트로 변환

    Args:
        audio_data: 음성 파일 바이너리 데이터 (WAV, MP3 등)
        client_id: Clova API Client ID
        client_secret: Clova API Client Secret
        lang: 언어 (Kor=한국어, Jpn=일본어, Eng=영어, Chn=중국어)

    Returns:
        str: 인식된 텍스트, 실패시 None

    Example:
        >>> with open('audio.wav', 'rb') as f:
        ...     audio_data = f.read()
        >>> text = clova_stt(audio_data, 'client_id', 'client_secret')
        >>> print(text)
        '삼성전자 10주 사줘'
    """
    url = f"https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang={lang}"

    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Content-Type": "application/octet-stream"
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=audio_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get('text', '')

            if text:
                print(f"✅ 음성 인식 성공: {text}")
                return text
            else:
                print("❌ 음성 인식 실패: 텍스트 없음")
                return None
        else:
            print(f"❌ 음성 인식 실패: HTTP {response.status_code}")
            print(f"   응답: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Clova STT 오류: {str(e)}")
        return None


def text_to_speech(text: str, lang: str = 'ko', slow: bool = False) -> io.BytesIO:
    """gTTS를 사용하여 텍스트를 음성으로 변환

    Args:
        text: 변환할 텍스트
        lang: 언어 (ko=한국어, en=영어, ja=일본어, zh-CN=중국어)
        slow: 느리게 말하기 (True/False)

    Returns:
        io.BytesIO: MP3 음성 데이터 (메모리 버퍼)

    Example:
        >>> audio_fp = text_to_speech("안녕하세요")
        >>> # Flask에서 send_file(audio_fp, mimetype='audio/mp3')
    """
    try:
        # gTTS로 음성 생성
        tts = gTTS(text=text, lang=lang, slow=slow)

        # 메모리에 저장 (파일 생성 안함)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        print(f"✅ TTS 생성 성공: {len(text)}자")
        return audio_fp

    except Exception as e:
        print(f"❌ TTS 생성 오류: {str(e)}")
        raise


def save_audio_file(audio_data: bytes, file_path: str) -> bool:
    """음성 데이터를 파일로 저장

    Args:
        audio_data: 음성 파일 바이너리 데이터
        file_path: 저장할 파일 경로

    Returns:
        bool: 성공 여부
    """
    try:
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        print(f"✅ 음성 파일 저장 성공: {file_path}")
        return True

    except Exception as e:
        print(f"❌ 파일 저장 오류: {str(e)}")
        return False


def load_audio_file(file_path: str) -> Optional[bytes]:
    """음성 파일 로드

    Args:
        file_path: 음성 파일 경로

    Returns:
        bytes: 음성 데이터, 실패시 None
    """
    try:
        with open(file_path, 'rb') as f:
            audio_data = f.read()
        print(f"✅ 음성 파일 로드 성공: {file_path}")
        return audio_data

    except Exception as e:
        print(f"❌ 파일 로드 오류: {str(e)}")
        return None


# ===== 테스트 함수 =====
def test_tts():
    """TTS 기능 테스트"""
    print("=" * 70)
    print("TTS (텍스트→음성) 테스트")
    print("=" * 70)

    test_texts = [
        "안녕하세요, AI 음성 매매 챗봇입니다.",
        "삼성전자 현재가는 72,500원입니다.",
        "매수 주문이 완료되었습니다.",
    ]

    for i, text in enumerate(test_texts, 1):
        print(f"\n[테스트 {i}] {text}")

        try:
            audio_fp = text_to_speech(text)
            print(f"   → 생성 성공! 크기: {len(audio_fp.getvalue())} bytes")

            # 파일로 저장 (선택사항)
            # save_audio_file(audio_fp.getvalue(), f'test_tts_{i}.mp3')

        except Exception as e:
            print(f"   → 생성 실패: {str(e)}")


def test_stt():
    """STT 기능 테스트 (실제 API 키 필요)"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    client_id = os.getenv('CLOVA_CLIENT_ID')
    client_secret = os.getenv('CLOVA_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("❌ .env 파일에 Clova API 키를 설정해주세요!")
        return

    print("=" * 70)
    print("STT (음성→텍스트) 테스트")
    print("=" * 70)

    # 테스트용 음성 파일이 필요합니다
    test_file = "test_audio.wav"

    if not os.path.exists(test_file):
        print(f"❌ 테스트 파일이 없습니다: {test_file}")
        print("   실제 음성 파일로 테스트해주세요.")
        return

    audio_data = load_audio_file(test_file)
    if audio_data:
        text = clova_stt(audio_data, client_id, client_secret)
        print(f"\n인식 결과: {text}")


if __name__ == "__main__":
    # TTS 테스트 (API 키 불필요)
    test_tts()

    print("\n" + "=" * 70 + "\n")

    # STT 테스트 (API 키 필요)
    # test_stt()
