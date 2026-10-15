# ☕ 전자정부프레임워크(eGovFrame) 백엔드 실행 & 연동 가이드

본 프로젝트의 백엔드는 **전자정부프레임워크 4.x 표준 아키텍처**와 **Spring Boot 3 + Java 17 + Oracle + MyBatis** 기반으로 구축되어 있습니다.

---

## 1. ⚙️ 사전 요구사항
- **Java**: JDK 17 이상 (`java -version`으로 확인)
- **Database**: Oracle XE 11g / 18c / 19c / 21c (또는 Docker Oracle)
  - 계정: `SMARTCITY_USER` / 암호: `SmartCity2024!` (또는 본인 DB 계정에 맞게 `application.yml` 수정)

---

## 2. 🗄️ 오라클 DB 초기화 및 대량 더미 데이터 입력
1. Oracle SQL Developer나 SQL*Plus를 열고 관리자 권한으로 계정 생성:
   ```sql
   CREATE USER SMARTCITY_USER IDENTIFIED BY "SmartCity2024!";
   GRANT CONNECT, RESOURCE, DBA TO SMARTCITY_USER;
   ```
2. 스키마 DDL 실행:
   - `db/schema_oracle.sql` 실행 (테이블, 시퀀스, 인덱스 생성)
3. 대용량 더미 데이터 생성 및 입력:
   ```bash
   # 파이썬으로 1,500건 이상 더미 데이터 생성
   python db/generate_dummy.py
   ```
   - 생성된 `db/dummy_data_insert.sql`을 SQL Developer에서 실행(F5)하여 커밋합니다.

---

## 3. 🚀 백엔드 서버 빌드 및 실행

Gradle Wrapper를 기본 내장하여 별도의 Maven/Gradle 설치 없이 즉시 실행할 수 있습니다.

```bash
cd backend

# 빌드 및 실행 (Windows PowerShell / CMD)
gradle bootRun
# 또는 IDE(IntelliJ IDEA, Eclipse eGovFrame IDE, VS Code)에서 SmartCityApplication.java 실행
```

서버가 구동되면 다음 엔드포인트에서 넥사크로 및 REST API를 제공합니다:
- **민원 페이징 조회 API**: `http://localhost:8080/api/complaints?page=1&pageSize=20`
- **시설물 목록 조회 API**: `http://localhost:8080/api/facilities`
- **민원 상세 및 조치 저장 API**: `http://localhost:8080/api/complaint/save`
- **Nexacro 트랜잭션 수신 Base URL**: `http://localhost:8080/api/nexacro/`

---

## 4. 🔗 Nexacro Studio 와의 연동
Nexacro Studio의 `Environment.xml`의 Service URL(`http://localhost:8080/api/nexacro/`)을 통해 이 백엔드와 연결되며, Form 화면에서 F5(Launch) 실행 시 실시간 Oracle DB 데이터가 넥사크로 Dataset에 바인딩됩니다.
