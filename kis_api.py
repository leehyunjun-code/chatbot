"""
한국투자증권 Open API 클래스
실제 주식 매매 및 조회를 위한 API 연동
"""

import requests
import json
from typing import Dict, Optional
from datetime import datetime


class KISApi:
    """한국투자증권 API 클래스"""

    def __init__(self, app_key: str, app_secret: str, account_no: str,
                 is_real: bool = False):
        """
        Args:
            app_key: API Key (한투에서 발급)
            app_secret: API Secret (한투에서 발급)
            account_no: 계좌번호 (8자리)
            is_real: 실전투자 여부 (True: 실전, False: 모의투자)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.account_product_cd = "01"  # 종합계좌
        self.is_real = is_real

        # API 엔드포인트
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"

        self.access_token = None

        # 토큰 발급
        self._get_access_token()

    def _get_access_token(self) -> None:
        """OAuth 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"

        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print("한국투자증권 API 토큰 발급 완료")
            else:
                raise Exception(f"토큰 발급 실패: {response.text}")

        except Exception as e:
            print(f"토큰 발급 오류: {str(e)}")
            raise

    def _get_headers(self, tr_id: str) -> Dict:
        """API 호출용 헤더 생성

        Args:
            tr_id: 거래 ID (API마다 다름)

        Returns:
            dict: 헤더 딕셔너리
        """
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P"  # 개인
        }

    def get_current_price(self, stock_code: str) -> Dict:
        """주식 현재가 조회

        Args:
            stock_code: 종목코드 (예: "005930")

        Returns:
            dict: {
                "success": True/False,
                "stock_name": "종목명",
                "current_price": 현재가,
                "change": 전일대비,
                "change_rate": 등락률,
                "volume": 거래량
            }
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

        tr_id = "FHKST01010100"
        headers = self._get_headers(tr_id)

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분 (J=주식)
            "FID_INPUT_ISCD": stock_code  # 종목코드
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data["rt_cd"] == "0":  # 성공
                    output = data["output"]
                    return {
                        "success": True,
                        "stock_name": output["hts_kor_isnm"],  # 종목명
                        "current_price": int(output["stck_prpr"]),  # 현재가
                        "change": int(output["prdy_vrss"]),  # 전일대비
                        "change_rate": float(output["prdy_ctrt"]),  # 등락률
                        "volume": int(output["acml_vol"])  # 거래량
                    }
                else:
                    return {
                        "success": False,
                        "message": f"조회 실패: {data.get('msg1', '알 수 없는 오류')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 오류: HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }

    def buy_stock(self, stock_code: str, quantity: int,
                  order_type: str = "시장가", price: int = 0) -> Dict:
        """주식 매수 주문

        Args:
            stock_code: 종목코드
            quantity: 수량
            order_type: "시장가" 또는 "지정가"
            price: 지정가 주문시 가격

        Returns:
            dict: {
                "success": True/False,
                "order_no": "주문번호",
                "message": "메시지"
            }
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        # TR_ID (매수 주문)
        if self.is_real:
            tr_id = "TTTC0802U"  # 실전투자
        else:
            tr_id = "VTTC0802U"  # 모의투자

        headers = self._get_headers(tr_id)

        # 주문구분: 01=시장가, 00=지정가
        if order_type == "시장가":
            ord_dvsn = "01"
            ord_unpr = "0"
        else:
            ord_dvsn = "00"
            ord_unpr = str(price)

        body = {
            "CANO": self.account_no,  # 계좌번호
            "ACNT_PRDT_CD": self.account_product_cd,  # 상품코드
            "PDNO": stock_code,  # 종목코드
            "ORD_DVSN": ord_dvsn,  # 주문구분
            "ORD_QTY": str(quantity),  # 주문수량
            "ORD_UNPR": ord_unpr  # 주문단가
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data["rt_cd"] == "0":  # 성공
                    return {
                        "success": True,
                        "order_no": data["output"]["ODNO"],
                        "message": f"매수 주문 성공 (주문번호: {data['output']['ODNO']})"
                    }
                else:  # 실패
                    return {
                        "success": False,
                        "message": f"매수 실패: {data.get('msg1', '알 수 없는 오류')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 오류: HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }

    def sell_stock(self, stock_code: str, quantity: int,
                   order_type: str = "시장가", price: int = 0) -> Dict:
        """주식 매도 주문

        Args:
            stock_code: 종목코드
            quantity: 수량 (-1이면 전량 매도)
            order_type: "시장가" 또는 "지정가"
            price: 지정가 주문시 가격

        Returns:
            dict: {
                "success": True/False,
                "order_no": "주문번호",
                "message": "메시지"
            }
        """
        # 전량 매도인 경우 보유 수량 조회
        if quantity == -1:
            holdings = self.get_holdings()
            if holdings["success"]:
                for stock in holdings["holdings"]:
                    if stock["stock_code"] == stock_code:
                        quantity = stock["quantity"]
                        break
                else:
                    return {
                        "success": False,
                        "message": "해당 종목을 보유하고 있지 않습니다."
                    }
            else:
                return {
                    "success": False,
                    "message": "보유 종목 조회에 실패했습니다."
                }

        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        # TR_ID (매도 주문 - 매수와 다름!)
        if self.is_real:
            tr_id = "TTTC0801U"  # 실전투자
        else:
            tr_id = "VTTC0801U"  # 모의투자

        headers = self._get_headers(tr_id)

        # 주문구분
        if order_type == "시장가":
            ord_dvsn = "01"
            ord_unpr = "0"
        else:
            ord_dvsn = "00"
            ord_unpr = str(price)

        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_cd,
            "PDNO": stock_code,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": ord_unpr
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data["rt_cd"] == "0":
                    return {
                        "success": True,
                        "order_no": data["output"]["ODNO"],
                        "message": f"매도 주문 성공 (주문번호: {data['output']['ODNO']})"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"매도 실패: {data.get('msg1', '알 수 없는 오류')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 오류: HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }

    def get_balance(self) -> Dict:
        """예수금 및 계좌 잔고 조회

        Returns:
            dict: {
                "success": True/False,
                "deposit": 예수금,
                "total_value": 총평가금액,
                "profit_loss": 평가손익,
                "profit_rate": 수익률
            }
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"

        # TR_ID
        if self.is_real:
            tr_id = "TTTC8908R"  # 실전투자
        else:
            tr_id = "VTTC8908R"  # 모의투자

        headers = self._get_headers(tr_id)

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_cd,
            "PDNO": "",  # 전체
            "ORD_UNPR": "0",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data["rt_cd"] == "0":
                    output = data["output"]
                    return {
                        "success": True,
                        "deposit": int(output.get("dnca_tot_amt", 0)),  # 예수금
                        "total_value": int(output.get("tot_evlu_amt", 0)),  # 총평가금액
                        "profit_loss": int(output.get("evlu_pfls_smtl_amt", 0)),  # 평가손익
                        "profit_rate": float(output.get("tot_evlu_pfls_rt", 0))  # 수익률
                    }
                else:
                    return {
                        "success": False,
                        "message": f"조회 실패: {data.get('msg1', '알 수 없는 오류')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 오류: HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }

    def get_holdings(self) -> Dict:
        """보유 종목 조회

        Returns:
            dict: {
                "success": True/False,
                "holdings": [
                    {
                        "stock_name": "종목명",
                        "stock_code": "종목코드",
                        "quantity": 보유수량,
                        "avg_price": 평균매입가,
                        "current_price": 현재가,
                        "profit_loss": 평가손익,
                        "profit_rate": 수익률
                    },
                    ...
                ],
                "count": 보유종목수
            }
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

        # TR_ID
        if self.is_real:
            tr_id = "TTTC8434R"  # 실전투자
        else:
            tr_id = "VTTC8434R"  # 모의투자

        headers = self._get_headers(tr_id)

        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.account_product_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data["rt_cd"] == "0":
                    holdings = []

                    for item in data["output1"]:
                        qty = int(item.get("hldg_qty", 0))
                        if qty > 0:  # 보유수량이 있는 것만
                            holdings.append({
                                "stock_name": item.get("prdt_name", ""),  # 종목명
                                "stock_code": item.get("pdno", ""),  # 종목코드
                                "quantity": qty,  # 보유수량
                                "avg_price": int(item.get("pchs_avg_pric", 0)),  # 평균매입가
                                "current_price": int(item.get("prpr", 0)),  # 현재가
                                "profit_loss": int(item.get("evlu_pfls_amt", 0)),  # 평가손익
                                "profit_rate": float(item.get("evlu_pfls_rt", 0))  # 수익률
                            })

                    return {
                        "success": True,
                        "holdings": holdings,
                        "count": len(holdings)
                    }
                else:
                    return {
                        "success": False,
                        "message": f"조회 실패: {data.get('msg1', '알 수 없는 오류')}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 오류: HTTP {response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"네트워크 오류: {str(e)}"
            }


# ===== 테스트 함수 =====
def test_kis_api():
    """KIS API 테스트 (모의투자)"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    app_key = os.getenv('KIS_APP_KEY')
    app_secret = os.getenv('KIS_APP_SECRET')
    account_no = os.getenv('KIS_ACCOUNT_NO')

    if not all([app_key, app_secret, account_no]):
        print(".env 파일에 API 키를 설정해주세요!")
        return

    # API 초기화 (모의투자)
    api = KISApi(app_key, app_secret, account_no, is_real=False)

    print("\n" + "=" * 70)
    print("한국투자증권 API 테스트")
    print("=" * 70)

    # 1. 현재가 조회
    print("\n[1] 삼성전자 현재가 조회")
    result = api.get_current_price("005930")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 2. 잔고 조회
    print("\n[2] 계좌 잔고 조회")
    result = api.get_balance()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 3. 보유 종목 조회
    print("\n[3] 보유 종목 조회")
    result = api.get_holdings()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_kis_api()