-- ====================================================================
-- 프로젝트명 : 스마트시티 / 공공시설 통합 민원 및 시설물 관리 시스템
-- 데이터베이스 : Oracle 11g / 12c / 19c / 21c / XE 호환
-- 작성 목적 : 포트폴리오용 고성능 스키마 & 대용량 데이터 인덱스 최적화
-- ====================================================================

-- 1. 기존 테이블 및 시퀀스 정리 (필요 시 주석 해제 후 실행)
/*
DROP TABLE TB_IOT_SENSOR_LOG CASCADE CONSTRAINTS;
DROP TABLE TB_FACILITY_INSP CASCADE CONSTRAINTS;
DROP TABLE TB_CIVIL_COMPLAINT CASCADE CONSTRAINTS;
DROP TABLE TB_FACILITY CASCADE CONSTRAINTS;

DROP SEQUENCE SEQ_FACILITY;
DROP SEQUENCE SEQ_INSPECTION;
DROP SEQUENCE SEQ_COMPLAINT;
DROP SEQUENCE SEQ_SENSOR_LOG;
*/

-- 2. 시퀀스 생성 (대량 인서트 시 캐시 메모리를 넉넉히 주어 시퀀스 경합 최소화)
CREATE SEQUENCE SEQ_FACILITY START WITH 1 INCREMENT BY 1 CACHE 100 NOCYCLE;
CREATE SEQUENCE SEQ_INSPECTION START WITH 1 INCREMENT BY 1 CACHE 200 NOCYCLE;
CREATE SEQUENCE SEQ_COMPLAINT START WITH 1 INCREMENT BY 1 CACHE 200 NOCYCLE;
CREATE SEQUENCE SEQ_SENSOR_LOG START WITH 1 INCREMENT BY 1 CACHE 500 NOCYCLE;

-- ====================================================================
-- 3. 테이블 정의
-- ====================================================================

-- [3-1] 스마트시티 시설물 마스터 테이블
CREATE TABLE TB_FACILITY (
    FAC_ID          VARCHAR2(30)    NOT NULL,               -- 시설물 고유번호 (예: FAC-2024-0001)
    FAC_NAME        VARCHAR2(150)   NOT NULL,               -- 시설물명 (예: 강남대로 102 스마트가로등)
    FAC_TYPE        VARCHAR2(50)    NOT NULL,               -- 시설분류 (STREET_LIGHT, CCTV, SHELTER, EV_CHARGER, PUMP, BIKE_STATION)
    DISTRICT        VARCHAR2(50)    NOT NULL,               -- 관할 자치구 (강남구, 서초구, 마포구, 영등포구 등)
    LOCATION_ADDR   VARCHAR2(250)   NOT NULL,               -- 설치 위치 상세주소
    LATITUDE        NUMBER(10, 7)   NOT NULL,               -- 위도 (GPS Latitude: 37.xxx)
    LONGITUDE       NUMBER(10, 7)   NOT NULL,               -- 경도 (GPS Longitude: 126.xxx ~ 127.xxx)
    INSTALL_DATE    DATE            DEFAULT SYSDATE,        -- 설치 일자
    OP_STATUS       VARCHAR2(20)    DEFAULT 'NORMAL',       -- 운영상태 (NORMAL:정상, WARNING:점검필요, ERROR:고장, SHUTDOWN:중지)
    MANAGE_DEPT     VARCHAR2(50)    DEFAULT '도시시설관리과', -- 관리 부서
    MANAGER_NAME    VARCHAR2(50),                           -- 담당 관리자 성명
    MANAGER_PHONE   VARCHAR2(20),                           -- 담당자 연락처
    LAST_INSP_DATE  DATE,                                   -- 최종 점검 일자
    REMARKS         VARCHAR2(500),                          -- 비고
    CREATED_AT      DATE            DEFAULT SYSDATE,
    CONSTRAINT PK_TB_FACILITY PRIMARY KEY (FAC_ID)
);

COMMENT ON TABLE TB_FACILITY IS '스마트시티 공공시설물 마스터';
COMMENT ON COLUMN TB_FACILITY.FAC_ID IS '시설물 고유 식별자';
COMMENT ON COLUMN TB_FACILITY.FAC_TYPE IS '시설물 유형코드';
COMMENT ON COLUMN TB_FACILITY.OP_STATUS IS '운영 상태 (NORMAL, WARNING, ERROR, SHUTDOWN)';


-- [3-2] 시설물 점검 및 유지보수 이력 테이블
CREATE TABLE TB_FACILITY_INSP (
    INSP_ID         VARCHAR2(30)    NOT NULL,               -- 점검 번호 (예: INSP-2024-00001)
    FAC_ID          VARCHAR2(30)    NOT NULL,               -- 대상 시설물 ID
    INSP_DATE       DATE            DEFAULT SYSDATE,        -- 점검 일자
    INSP_TYPE       VARCHAR2(30)    DEFAULT 'REGULAR',      -- 점검 구분 (REGULAR:정기점검, EMERGENCY:긴급점검, COMPLAINT:민원조치)
    INSP_STATUS     VARCHAR2(20)    DEFAULT 'PASS',         -- 점검 결과 (PASS:양호, REPAIR:보수필요, FAIL:불량조치)
    INSPECTOR_NAME  VARCHAR2(50)    NOT NULL,               -- 점검원 이름
    ACTION_DETAILS  VARCHAR2(1000),                         -- 조치 상세 내역
    REPAIR_COST     NUMBER(12, 0)   DEFAULT 0,              -- 수리/조치 비용 (원)
    NEXT_INSP_DATE  DATE,                                   -- 차기 예정 점검일
    CONSTRAINT PK_TB_FACILITY_INSP PRIMARY KEY (INSP_ID),
    CONSTRAINT FK_INSP_FACILITY FOREIGN KEY (FAC_ID) REFERENCES TB_FACILITY(FAC_ID) ON DELETE CASCADE
);

COMMENT ON TABLE TB_FACILITY_INSP IS '시설물 유지보수 및 정기점검 이력';


-- [3-3] 스마트시티 시민 통합 민원 접수 및 처리 테이블
CREATE TABLE TB_CIVIL_COMPLAINT (
    COMPLAINT_ID    VARCHAR2(30)    NOT NULL,               -- 민원 접수번호 (예: CMP-2024-000001)
    TITLE           VARCHAR2(200)   NOT NULL,               -- 민원 제목
    CATEGORY        VARCHAR2(50)    NOT NULL,               -- 민원 분류 (도로파손, 가로등소등, 악취/소음, 불법주차, 스마트시설오작동 등)
    CONTENT         VARCHAR2(3000)  NOT NULL,               -- 민원 상세 내용
    PETITIONER_NAME VARCHAR2(50)    NOT NULL,               -- 민원인 성명 (마스킹 지원)
    PETITIONER_TEL  VARCHAR2(20),                           -- 민원인 연락처
    OCCUR_ADDRESS   VARCHAR2(250)   NOT NULL,               -- 민원 발생 위치
    DISTRICT        VARCHAR2(50)    NOT NULL,               -- 관할 자치구
    RELATED_FAC_ID  VARCHAR2(30),                           -- 연계 시설물 ID (선택)
    REG_DATE        DATE            DEFAULT SYSDATE,        -- 접수 일시
    STATUS          VARCHAR2(20)    DEFAULT 'RECEIVED',     -- 처리 상태 (RECEIVED:접수, ASSIGNED:담당배정, IN_PROGRESS:처리중, RESOLVED:해결완료, REJECTED:반려)
    ASSIGNED_DEPT   VARCHAR2(50),                           -- 배정 부서
    HANDLER_NAME    VARCHAR2(50),                           -- 처리 담당자
    RESOLVE_DATE    DATE,                                   -- 처리 완료 일시
    RESOLVE_COMMENT VARCHAR2(2000),                         -- 처리 결과 답변
    SATISFACTION    NUMBER(2, 0),                           -- 민원 만족도 평가 (1~5점)
    CONSTRAINT PK_TB_CIVIL_COMPLAINT PRIMARY KEY (COMPLAINT_ID),
    CONSTRAINT FK_COMPLAINT_FACILITY FOREIGN KEY (RELATED_FAC_ID) REFERENCES TB_FACILITY(FAC_ID) ON DELETE SET NULL
);

COMMENT ON TABLE TB_CIVIL_COMPLAINT IS '시민 통합 민원 접수 및 처리 데이터';
COMMENT ON COLUMN TB_CIVIL_COMPLAINT.STATUS IS '상태 (RECEIVED, ASSIGNED, IN_PROGRESS, RESOLVED, REJECTED)';


-- [3-4] IoT 센서 실시간 계측 로그 (대용량 시계열 데이터)
CREATE TABLE TB_IOT_SENSOR_LOG (
    LOG_ID          NUMBER(15)      NOT NULL,               -- 로그 고유번호
    FAC_ID          VARCHAR2(30)    NOT NULL,               -- 시설물 ID
    SENSOR_TYPE     VARCHAR2(30)    NOT NULL,               -- 센서 유형 (TEMP_HUMID, VIBRATION, POWER_KWH, DUST, TILT)
    METRIC_VAL      NUMBER(10, 2)   NOT NULL,               -- 측정 수치
    UNIT            VARCHAR2(20)    NOT NULL,               -- 단위 (℃, %, g, kWh, ㎍/㎥, deg)
    STATUS_FLAG     VARCHAR2(10)    DEFAULT 'OK',           -- 상태 플래그 (OK:정상, WARN:주의, DANGER:위험)
    LOGGED_AT       TIMESTAMP       DEFAULT SYSTIMESTAMP,   -- 계측 시간
    CONSTRAINT PK_TB_IOT_SENSOR_LOG PRIMARY KEY (LOG_ID),
    CONSTRAINT FK_LOG_FACILITY FOREIGN KEY (FAC_ID) REFERENCES TB_FACILITY(FAC_ID) ON DELETE CASCADE
);

COMMENT ON TABLE TB_IOT_SENSOR_LOG IS '시설물 부착 IoT 센서 실시간 텔레메트리 로그';


-- ====================================================================
-- 4. 대용량 데이터 성능 최적화를 위한 인덱스 설계
-- ====================================================================

-- [4-1] 시설물 복합 인덱스 (구역별 + 시설유형별 + 운영상태 필터링)
CREATE INDEX IDX_FACILITY_SEARCH ON TB_FACILITY (DISTRICT, FAC_TYPE, OP_STATUS);

-- [4-2] 민원 접수일자 + 상태 역순 인덱스 (대시보드 최근 민원 조회 및 페이징 전용)
CREATE INDEX IDX_COMPLAINT_PAGE ON TB_CIVIL_COMPLAINT (STATUS, REG_DATE DESC);

-- [4-3] 자치구별 민원 집계용 인덱스
CREATE INDEX IDX_COMPLAINT_DIST ON TB_CIVIL_COMPLAINT (DISTRICT, REG_DATE);

-- [4-4] 시설물 점검일자 역순 인덱스
CREATE INDEX IDX_INSP_DATE_DESC ON TB_FACILITY_INSP (INSP_DATE DESC);

-- [4-5] IoT 센서 로그 복합 인덱스 (특정 시설물의 최근 센서값 조회용)
CREATE INDEX IDX_SENSOR_FAC_TIME ON TB_IOT_SENSOR_LOG (FAC_ID, LOGGED_AT DESC);

COMMIT;
