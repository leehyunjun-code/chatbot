"""
MySQL 데이터베이스 연동 클래스
주문 내역, 채팅 로그 등을 저장 및 조회
"""

import pymysql
from contextlib import contextmanager
from typing import List, Dict, Optional
from datetime import datetime


class Database:
    """MySQL 데이터베이스 클래스"""

    def __init__(self, host: str = 'localhost', user: str = 'root',
                 password: str = '', database: str = 'stock_chatbot',
                 port: int = 3306):
        """
        Args:
            host: MySQL 호스트 (기본: localhost)
            user: MySQL 사용자 (기본: root)
            password: MySQL 비밀번호
            database: 데이터베이스 이름 (기본: stock_chatbot)
            port: MySQL 포트 (기본: 3306)
        """
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    @contextmanager
    def get_connection(self):
        """DB 연결 컨텍스트 매니저

        Usage:
            with db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users")
        """
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"❌ DB 오류: {str(e)}")
            raise e
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트

        Returns:
            bool: 연결 성공 여부
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result:
                        print("✅ 데이터베이스 연결 성공")
                        return True
            return False
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {str(e)}")
            return False

    # ===== 사용자 관련 =====

    def create_user(self, username: str) -> int:
        """사용자 생성

        Args:
            username: 사용자 이름

        Returns:
            int: 생성된 사용자 ID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO users (username) VALUES (%s)"
                cursor.execute(sql, (username,))
                return cursor.lastrowid

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """사용자 조회

        Args:
            user_id: 사용자 ID

        Returns:
            dict: 사용자 정보, 없으면 None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()

    # ===== 주문 관련 =====

    def save_order(self, user_id: int, order_data: Dict) -> int:
        """주문 내역 저장

        Args:
            user_id: 사용자 ID
            order_data: 주문 정보 딕셔너리
                {
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "action": "매수",
                    "quantity": 10,
                    "price_type": "시장가",
                    "order_price": 0,
                    "order_no": "1234567890"
                }

        Returns:
            int: 생성된 주문 ID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO orders (
                    user_id, stock_code, stock_name, action,
                    quantity, price_type, order_price, status, order_no
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """
                cursor.execute(sql, (
                    user_id,
                    order_data.get('stock_code', ''),
                    order_data.get('stock_name', ''),
                    order_data.get('action', ''),
                    order_data.get('quantity', 0),
                    order_data.get('price_type', '시장가'),
                    order_data.get('order_price', 0),
                    '대기',  # 초기 상태
                    order_data.get('order_no', '')
                ))
                return cursor.lastrowid

    def update_order_status(self, order_id: int, status: str,
                           filled_price: Optional[float] = None) -> bool:
        """주문 상태 업데이트

        Args:
            order_id: 주문 ID
            status: 상태 ("대기", "체결", "취소")
            filled_price: 체결가격 (체결시에만)

        Returns:
            bool: 성공 여부
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                if filled_price is not None:
                    sql = """
                    UPDATE orders
                    SET status = %s, filled_price = %s, filled_time = NOW()
                    WHERE id = %s
                    """
                    cursor.execute(sql, (status, filled_price, order_id))
                else:
                    sql = "UPDATE orders SET status = %s WHERE id = %s"
                    cursor.execute(sql, (status, order_id))

                return cursor.rowcount > 0

    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """사용자 주문 내역 조회

        Args:
            user_id: 사용자 ID
            limit: 조회할 개수 (기본: 10)

        Returns:
            list: 주문 목록
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM orders
                WHERE user_id = %s
                ORDER BY order_time DESC
                LIMIT %s
                """
                cursor.execute(sql, (user_id, limit))
                return cursor.fetchall()

    def get_order_by_id(self, order_id: int) -> Optional[Dict]:
        """주문 조회

        Args:
            order_id: 주문 ID

        Returns:
            dict: 주문 정보, 없으면 None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM orders WHERE id = %s"
                cursor.execute(sql, (order_id,))
                return cursor.fetchone()

    def get_orders_by_stock(self, user_id: int, stock_code: str) -> List[Dict]:
        """특정 종목의 주문 내역 조회

        Args:
            user_id: 사용자 ID
            stock_code: 종목코드

        Returns:
            list: 주문 목록
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM orders
                WHERE user_id = %s AND stock_code = %s
                ORDER BY order_time DESC
                """
                cursor.execute(sql, (user_id, stock_code))
                return cursor.fetchall()

    # ===== 채팅 로그 관련 =====

    def save_chat_log(self, user_id: int, message: str, sender: str) -> int:
        """채팅 로그 저장

        Args:
            user_id: 사용자 ID
            message: 메시지 내용
            sender: 발신자 ("user" 또는 "bot")

        Returns:
            int: 생성된 로그 ID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO chat_logs (user_id, message, sender)
                VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (user_id, message, sender))
                return cursor.lastrowid

    def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """채팅 기록 조회

        Args:
            user_id: 사용자 ID
            limit: 조회할 개수 (기본: 50)

        Returns:
            list: 채팅 로그 목록
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM chat_logs
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """
                cursor.execute(sql, (user_id, limit))
                results = cursor.fetchall()
                # 오래된 순서로 반환
                return list(reversed(results))

    def delete_old_chat_logs(self, days: int = 30) -> int:
        """오래된 채팅 로그 삭제

        Args:
            days: 삭제할 로그의 기준 일수 (기본: 30일)

        Returns:
            int: 삭제된 로그 개수
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                DELETE FROM chat_logs
                WHERE timestamp < DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                cursor.execute(sql, (days,))
                return cursor.rowcount

    # ===== 통계 =====

    def get_order_statistics(self, user_id: int) -> Dict:
        """주문 통계 조회

        Args:
            user_id: 사용자 ID

        Returns:
            dict: {
                "total_orders": 전체 주문 수,
                "buy_orders": 매수 주문 수,
                "sell_orders": 매도 주문 수,
                "completed_orders": 체결 완료 수,
                "pending_orders": 대기 중 수,
                "canceled_orders": 취소 수
            }
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT
                    COUNT(*) as total_orders,
                    SUM(CASE WHEN action = '매수' THEN 1 ELSE 0 END) as buy_orders,
                    SUM(CASE WHEN action = '매도' THEN 1 ELSE 0 END) as sell_orders,
                    SUM(CASE WHEN status = '체결' THEN 1 ELSE 0 END) as completed_orders,
                    SUM(CASE WHEN status = '대기' THEN 1 ELSE 0 END) as pending_orders,
                    SUM(CASE WHEN status = '취소' THEN 1 ELSE 0 END) as canceled_orders
                FROM orders
                WHERE user_id = %s
                """
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                return result if result else {}


# ===== 테스트 함수 =====
def test_database():
    """데이터베이스 기능 테스트"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # 환경변수에서 설정 로드
    db = Database(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'stock_chatbot'),
        port=int(os.getenv('DB_PORT', 3306))
    )

    print("=" * 70)
    print("데이터베이스 연결 테스트")
    print("=" * 70)

    # 연결 테스트
    if not db.test_connection():
        print("\n❌ 데이터베이스에 연결할 수 없습니다.")
        print("   MySQL이 실행 중인지, .env 설정이 올바른지 확인하세요.")
        return

    print("\n✅ 모든 기능이 정상 작동합니다!")


if __name__ == "__main__":
    test_database()
