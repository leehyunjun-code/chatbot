-- =====================================================
-- AI 음성 주식매매 챗봇 데이터베이스 스키마
-- =====================================================

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS stock_chatbot
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE stock_chatbot;

-- =====================================================
-- 1. 사용자 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '사용자 ID',
    username VARCHAR(50) NOT NULL COMMENT '사용자 이름',
    api_key VARCHAR(500) COMMENT '암호화된 API 키',
    api_secret VARCHAR(500) COMMENT '암호화된 API Secret',
    account_no VARCHAR(200) COMMENT '암호화된 계좌번호',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '가입일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',

    INDEX idx_username (username),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='사용자 정보';

-- =====================================================
-- 2. 주문 내역 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '주문 ID',
    user_id INT NOT NULL COMMENT '사용자 ID',
    stock_code VARCHAR(10) NOT NULL COMMENT '종목코드 (예: 005930)',
    stock_name VARCHAR(50) NOT NULL COMMENT '종목명 (예: 삼성전자)',
    action VARCHAR(10) NOT NULL COMMENT '매수/매도',
    quantity INT NOT NULL COMMENT '주문 수량',
    price_type VARCHAR(20) DEFAULT '시장가' COMMENT '시장가/지정가',
    order_price DECIMAL(15, 2) DEFAULT 0 COMMENT '주문 가격',
    filled_price DECIMAL(15, 2) COMMENT '체결 가격',
    status VARCHAR(20) DEFAULT '대기' COMMENT '대기/체결/취소',
    order_no VARCHAR(50) COMMENT '한투 API 주문번호',
    order_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '주문 시간',
    filled_time DATETIME COMMENT '체결 시간',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_action (action),
    INDEX idx_status (status),
    INDEX idx_order_time (order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='주문 내역';

-- =====================================================
-- 3. 채팅 로그 테이블
-- =====================================================
CREATE TABLE IF NOT EXISTS chat_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '로그 ID',
    user_id INT NOT NULL COMMENT '사용자 ID',
    message TEXT NOT NULL COMMENT '메시지 내용',
    sender VARCHAR(10) NOT NULL COMMENT 'user 또는 bot',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '전송 시간',

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_sender (sender),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='채팅 로그';

-- =====================================================
-- 4. 기본 사용자 생성 (테스트용)
-- =====================================================
INSERT INTO users (username) VALUES ('test_user')
ON DUPLICATE KEY UPDATE username = 'test_user';

-- =====================================================
-- 5. 데이터 확인
-- =====================================================
SELECT
    'users' as table_name,
    COUNT(*) as row_count
FROM users

UNION ALL

SELECT
    'orders' as table_name,
    COUNT(*) as row_count
FROM orders

UNION ALL

SELECT
    'chat_logs' as table_name,
    COUNT(*) as row_count
FROM chat_logs;

-- =====================================================
-- 완료 메시지
-- =====================================================
SELECT '✅ 데이터베이스 스키마 생성 완료!' as message;
