"""
Supabase 데이터베이스 연동 클래스
주문 내역, 채팅 로그 등을 저장 및 조회
"""

from supabase import create_client, Client
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Supabase 데이터베이스 클래스"""

    def __init__(self):
        """Supabase 클라이언트 초기화"""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_KEY')  # service_key 사용 (RLS 우회)
        
        if not url or not key:
            raise ValueError("Supabase URL과 KEY가 .env 파일에 설정되어 있지 않습니다.")
        
        self.supabase: Client = create_client(url, key)
        print("Supabase 연결 성공")

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            # users 테이블에서 1개 행만 조회
            response = self.supabase.table('users').select("*").limit(1).execute()
            print("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            print(f"데이터베이스 연결 실패: {str(e)}")
            return False

    # ===== 사용자 관련 =====

    def create_user(self, username: str) -> int:
        """사용자 생성"""
        try:
            response = self.supabase.table('users').insert({
                'username': username
            }).execute()
            return response.data[0]['id']
        except Exception as e:
            print(f"사용자 생성 오류: {str(e)}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """사용자 조회"""
        try:
            response = self.supabase.table('users').select("*").eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"사용자 조회 오류: {str(e)}")
            return None

    # ===== 주문 관련 =====

    def save_order(self, user_id: int, order_data: Dict) -> int:
        """주문 내역 저장"""
        try:
            response = self.supabase.table('orders').insert({
                'user_id': user_id,
                'stock_code': order_data.get('stock_code', ''),
                'stock_name': order_data.get('stock_name', ''),
                'action': order_data.get('action', ''),
                'quantity': order_data.get('quantity', 0),
                'price_type': order_data.get('price_type', '시장가'),
                'order_price': order_data.get('order_price', 0),
                'status': '대기',
                'order_no': order_data.get('order_no', '')
            }).execute()
            return response.data[0]['id']
        except Exception as e:
            print(f"주문 저장 오류: {str(e)}")
            return None

    def update_order_status(self, order_id: int, status: str,
                           filled_price: Optional[float] = None) -> bool:
        """주문 상태 업데이트"""
        try:
            update_data = {'status': status}
            
            if filled_price is not None:
                update_data['filled_price'] = filled_price
                update_data['filled_time'] = datetime.now().isoformat()
            
            response = self.supabase.table('orders').update(update_data).eq('id', order_id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"주문 상태 업데이트 오류: {str(e)}")
            return False

    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자 주문 내역 조회"""
        try:
            response = self.supabase.table('orders').select("*").eq(
                'user_id', user_id
            ).order('order_time', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"주문 조회 오류: {str(e)}")
            return []

    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """주문 조회"""
        try:
            response = self.supabase.table('orders').select("*").eq('id', order_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"주문 조회 오류: {str(e)}")
            return None

    def get_orders_by_stock(self, user_id: int, stock_code: str) -> List[Dict]:
        """특정 종목의 주문 내역 조회"""
        try:
            response = self.supabase.table('orders').select("*").eq(
                'user_id', user_id
            ).eq(
                'stock_code', stock_code
            ).order('order_time', desc=True).execute()
            return response.data
        except Exception as e:
            print(f"종목별 주문 조회 오류: {str(e)}")
            return []

    # ===== 채팅 로그 관련 =====

    def save_chat_log(self, user_id: int, message: str, sender: str) -> int:
        """채팅 로그 저장"""
        try:
            response = self.supabase.table('chat_logs').insert({
                'user_id': user_id,
                'message': message,
                'sender': sender
            }).execute()
            return response.data[0]['id']
        except Exception as e:
            print(f"채팅 로그 저장 오류: {str(e)}")
            return None

    def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """채팅 기록 조회"""
        try:
            response = self.supabase.table('chat_logs').select("*").eq(
                'user_id', user_id
            ).order('timestamp', desc=False).limit(limit).execute()
            return response.data
        except Exception as e:
            print(f"채팅 기록 조회 오류: {str(e)}")
            return []

    def delete_old_chat_logs(self, days: int = 30) -> int:
        """오래된 채팅 로그 삭제"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.supabase.table('chat_logs').delete().lt(
                'timestamp', cutoff_date
            ).execute()
            return len(response.data)
        except Exception as e:
            print(f"채팅 로그 삭제 오류: {str(e)}")
            return 0

    # ===== 통계 =====

    def get_order_statistics(self, user_id: int) -> Dict:
        """주문 통계 조회"""
        try:
            # 전체 주문 조회
            response = self.supabase.table('orders').select("*").eq('user_id', user_id).execute()
            orders = response.data
            
            if not orders:
                return {
                    "total_orders": 0,
                    "buy_orders": 0,
                    "sell_orders": 0,
                    "completed_orders": 0,
                    "pending_orders": 0,
                    "canceled_orders": 0
                }
            
            # 통계 계산
            stats = {
                "total_orders": len(orders),
                "buy_orders": len([o for o in orders if o['action'] == '매수']),
                "sell_orders": len([o for o in orders if o['action'] == '매도']),
                "completed_orders": len([o for o in orders if o['status'] == '체결']),
                "pending_orders": len([o for o in orders if o['status'] == '대기']),
                "canceled_orders": len([o for o in orders if o['status'] == '취소'])
            }
            
            return stats
        except Exception as e:
            print(f"통계 조회 오류: {str(e)}")
            return {}


# ===== 테스트 함수 =====
def test_database():
    """데이터베이스 기능 테스트"""
    print("=" * 70)
    print("Supabase 데이터베이스 연결 테스트")
    print("=" * 70)
    
    try:
        # Database 인스턴스 생성
        db = Database()
        
        # 연결 테스트
        if db.test_connection():
            print("\n모든 기능이 정상 작동합니다!")
            
            # 테스트 데이터 생성
            print("\n[테스트] 채팅 로그 저장...")
            db.save_chat_log(1, "테스트 메시지", "user")
            print("채팅 로그 저장 성공")
            
            # 조회 테스트
            print("\n[테스트] 채팅 기록 조회...")
            history = db.get_chat_history(1, limit=5)
            print(f"최근 채팅 {len(history)}개 조회 성공")
            
        else:
            print("\n데이터베이스 연결 실패")
            
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        print("   .env 파일의 SUPABASE_URL과 SUPABASE_SERVICE_KEY를 확인하세요.")


if __name__ == "__main__":
    test_database()