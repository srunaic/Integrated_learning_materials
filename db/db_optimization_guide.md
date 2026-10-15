# 🏛️ 스마트시티 대용량 DB 관리 및 PC 성능 보호 가이드 (Oracle 기반)

포트폴리오 프로젝트에서 실제 Oracle DB와 수천~수십만 건의 대량 가상 데이터를 운용할 때, 개발용 PC가 느려지거나 메모리가 고갈되지 않도록 관리하는 핵심 엔지니어링 가이드입니다.

---

## 1. 🚀 로컬 환경에서 Oracle 실행 권장 2가지 방법

### 방법 A: Docker를 이용한 경량 오라클 컨테이너 실행 (⭐ 가장 추천)
로컬 윈도우 OS의 서비스를 오염시키지 않고, 필요할 때만 켜고 끌 수 있어 PC 리소스를 가장 안전하게 지킵니다.

```bash
# 1. Oracle 19c or 21c Express Edition(XE) 경량 컨테이너 실행
# 메모리를 2GB로 딱 제한하여 PC 버벅임 원천 차단!
docker run -d --name smartcity-oracle \
  -p 1521:1521 -p 5500:5500 \
  -e ORACLE_PWD=SmartCity2024! \
  --memory="2g" \
  --memory-swap="3g" \
  gvenzl/oracle-xe:21-slim
```

### 방법 B: 윈도우 설치형 Oracle XE (Express Edition) 사용 시
오라클이 백그라운드 윈도우 서비스(`OracleServiceXE`, `OracleOraDB21Home1TNSListener`)로 상시 켜져 있으면 RAM을 3~4GB 이상 지속 점유합니다.
- **팁**: 윈도우 서비스 관리자(`services.msc`)에서 오라클 서비스의 시작 유형을 **'수동(Manual)'**으로 변경하고, 프로젝트 작업할 때만 아래 스크립트로 시작/종료하십시오.

```bat
:: [오라클 시작용 배치 파일] start_oracle.bat
net start OracleOraDB21Home1TNSListener
net start OracleServiceXE

:: [오라클 종료용 배치 파일] stop_oracle.bat
net stop OracleServiceXE
net stop OracleOraDB21Home1TNSListener
```

---

## 2. ⚡ PC가 느려지지 않는 오라클 메모리(SGA/PGA) 다이어트 설정

오라클 SQL*Plus 또는 SQL Developer에서 `SYS as SYSDBA`로 접속하여 오라클 내부 메모리 한도를 1GB~1.5GB 내외로 고정합니다.

```sql
-- 오라클 메모리 자동 관리 설정 (최대 메모리 1.5GB로 제한)
ALTER SYSTEM SET MEMORY_TARGET = 1536M SCOPE = SPFILE;
ALTER SYSTEM SET PGA_AGGREGATE_TARGET = 512M SCOPE = SPFILE;
ALTER SYSTEM SET SGA_TARGET = 1024M SCOPE = SPFILE;

-- 세션 최대 연결 수 제한 (불필요한 세션 누수 방지)
ALTER SYSTEM SET PROCESSES = 150 SCOPE = SPFILE;

-- 인스턴스 재시작 필요 시:
-- SHUTDOWN IMMEDIATE;
-- STARTUP;
```

---

## 3. 🎯 대용량 조회 시 백엔드 & DB 최적화 (페이징 필수!)

데이터가 10만 건 이상일 때 `SELECT * FROM TB_CIVIL_COMPLAINT`를 호출하면 백엔드 힙 메모리(Java OutOfMemoryError)와 브라우저 렉이 발생합니다.
반드시 **인덱스를 활용한 페이징(Pagination)**을 적용해야 합니다.

### [MyBatis / Oracle 12c+ 권장 페이징 쿼리]
```sql
SELECT 
    COMPLAINT_ID,
    TITLE,
    CATEGORY,
    PETITIONER_NAME,
    DISTRICT,
    STATUS,
    REG_DATE
FROM TB_CIVIL_COMPLAINT
ORDER BY REG_DATE DESC
OFFSET #{offset} ROWS FETCH NEXT #{pageSize} ROWS ONLY;
```

### [Oracle 11g 레거시 호환 ROWNUM 페이징 (전자정부프레임워크 표준)]
```sql
SELECT * FROM (
    SELECT 
        ROWNUM AS RNUM, 
        A.*
    FROM (
        /*+ INDEX_DESC(TB_CIVIL_COMPLAINT IDX_COMPLAINT_PAGE) */
        SELECT 
            COMPLAINT_ID, TITLE, CATEGORY, PETITIONER_NAME, DISTRICT, STATUS, REG_DATE
        FROM TB_CIVIL_COMPLAINT
        WHERE STATUS = NVL(#{status}, STATUS)
        ORDER BY REG_DATE DESC
    ) A
    WHERE ROWNUM <= #{endRow}
)
WHERE RNUM >= #{startRow};
```

---

## 4. 🛠️ Python Faker 대량 데이터 생성 명령어 모음

`db/generate_dummy.py`는 메모리를 적게 먹는 배치 커밋 구조로 설계되어 있습니다.

```bash
# 기본 모드 (시설물 150건, 민원 2,500건, 점검 500건, 센서 8,000건)
python db/generate_dummy.py

# 가벼운 테스트 모드 (PC 성능을 최우선으로 할 때)
python db/generate_dummy.py --facilities 50 --complaints 500 --inspections 100 --sensors 1000

# 대용량 스트레스 테스트 모드 (1만건 민원 생성)
python db/generate_dummy.py --facilities 300 --complaints 10000 --inspections 2000 --sensors 20000
```
생성된 `db/dummy_data_insert.sql` 파일은 Oracle SQL Developer에서 전체 선택 후 `F5(스크립트 실행)`를 누르면 일괄 삽입됩니다.
