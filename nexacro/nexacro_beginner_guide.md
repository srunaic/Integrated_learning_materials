# 📘 초보자를 위한 Nexacro N 설치 및 시작 가이드

환영합니다! 넥사크로(Nexacro)는 대한민국 공공기관, 지자체, 금융권 및 대기업 행정/업무 시스템에서 가장 많이 사용되는 **엔터프라이즈 No.1 UI/UX 프레임워크**입니다.

이 가이드는 넥사크로를 처음 접하는 분도 10분 안에 설치하고 프로젝트를 열어볼 수 있도록 단계별로 작성되었습니다.

---

## 1. 📥 Nexacro Studio 무료 체험판 다운로드 및 설치

넥사크로 화면 개발 툴은 **Nexacro Studio**입니다. 투비소프트 공식 고객지원센터에서 무료 체험판(Trial)을 제공합니다.

1. **다운로드 사이트 접속**:
   - 투비소프트 기술지원포털: [http://support.tobesoft.co.kr](http://support.tobesoft.co.kr)
   - 또는 넥사크로 체험판 다운로드 페이지: [https://www.tobesoft.com/product/nexacro.do](https://www.tobesoft.com/product/nexacro.do)
2. **Nexacro N Studio (최신) 또는 Nexacro 17 설치**:
   - 설치 프로그램(`NexacroN_SetupStudio.exe`)을 다운로드하여 기본 옵션으로 설치합니다.
   - 처음 실행 시 체험판 라이선스키(Trial Key)를 입력하거나 무료 시험 모드를 선택합니다.

---

## 2. 🧩 넥사크로 핵심 개념 3가지만 기억하세요!

넥사크로는 React나 일반 웹 개발과 조금 다르게 **"데이터 중심(Data-driven)"**으로 동작합니다.

| 개념 | 설명 | 비유 |
|---|---|---|
| **1. Dataset (데이터셋)** | 메모리상에 존재하는 가상 데이터 테이블. 컬럼(Column)과 행(Row)으로 구성되며, 사용자가 수정한 상태(`I`:추가, `U`:수정, `D`:삭제)를 자동으로 기억합니다. | 브라우저 안의 엑셀 시트 |
| **2. Grid (그리드)** | Dataset을 연결(Binding)하기만 하면 자동으로 표 형태로 화면에 렌더링하고 정렬, 셀렉트, 페이징을 해주는 핵심 컴포넌트입니다. | 엑셀 표 뷰어 |
| **3. Transaction (통신)** | 백엔드(전자정부프레임워크) 서버로 Dataset을 전송하고, DB에서 가져온 Dataset을 수신하는 비동기 통신 메서드입니다. | Ajax / Fetch의 넥사크로 버전 |

---

## 3. 📂 이번 프로젝트의 넥사크로 소스 구조

이 저장소의 `nexacro/` 폴더는 실제 Nexacro Studio 프로젝트로 구성되어 있습니다.

```
nexacro/
├── Environment.xml            # 넥사크로 전역 환경 설정 (Screen, Service URL 정의)
├── TypeDefinition.xml         # 컴포넌트 모듈 등록 정의
├── Application_Desktop.xadl   # 데스크톱 애플리케이션 시작점
├── appvariables.xml           # 글로벌 변수 및 공통 코드 데이터셋
└── project/
    ├── form/
    │   ├── MainDashboard.xfdl # 스마트시티 종합 관제 대시보드 화면
    │   ├── CivilComplaint.xfdl# 시민 통합 민원 접수 및 처리 화면
    │   └── FacilityMgmt.xfdl  # 공공 시설물 마스터 및 점검 이력 화면
    └── theme/                 # 공공 표준 스마트시티 UI 테마 (CSS)
```

---

## 4. 🚀 Nexacro Studio에서 프로젝트 열고 실행하는 방법

1. **Nexacro Studio 실행**
2. 상단 메뉴: **File -> Open -> Project...** 클릭
3. `d:\Github\egovoframework_nexacro\nexacro\Application_Desktop.xadl` 파일 선택
4. 좌측 **Project Explorer** 트리에서:
   - `project > form > CivilComplaint.xfdl` 더블 클릭
   - 화면에 그리드, 검색조건 바, 입력 폼이 시각적(WYSIWYG)으로 열립니다!
5. **실행 (미리보기)**:
   - 상단 메뉴의 **QuickView (단축키 Ctrl + F6)** 또는 **Launch (F5)** 클릭
   - 브라우저나 NRE(Nexacro Runtime Environment) 창이 뜨며 실제 동작하는 화면을 볼 수 있습니다.

---

## 5. 🔄 전자정부프레임워크(eGovFrame) 백엔드와 데이터 주고받기 (Transaction 원리)

넥사크로 스크립트에서 백엔드로 데이터를 요청하는 표준 코드는 다음과 같습니다:

```javascript
// 민원 목록 조회 함수 예시
this.fn_searchComplaint = function() {
    var strSvcId    = "selectComplaintList";
    var strSvcUrl   = "http://localhost:8080/api/nexacro/complaints";
    var inDataSets  = "ds_search=ds_search";       // 백엔드로 보낼 검색조건 데이터셋
    var outDataSets = "ds_complaints=ds_complaints"; // 서버로부터 받을 결과 데이터셋
    var strArg      = "user_id=admin";             // 추가 파라미터
    var callBackFnc = "fn_callback";               // 완료 후 실행할 콜백 함수

    // 넥사크로 표준 트랜잭션 호출
    this.transaction(strSvcId, strSvcUrl, inDataSets, outDataSets, strArg, callBackFnc);
};

// 콜백 함수
this.fn_callback = function(svcId, errCode, errMsg) {
    if (errCode < 0) {
        this.alert("조회 실패: " + errMsg);
        return;
    }
    // 조회 완료 후 그리드 자동 갱신됨
    trace("조회 성공! 데이터 건수: " + this.ds_complaints.getRowCount());
};
```

---

## 6. 🌐 웹 브라우저 / GitHub Pages 배포 연동 안내

- Nexacro Studio의 상단 메뉴 **Generate -> Application**을 실행하면, 작성한 XFDL이 순수 JavaScript/HTML5 코드로 컴파일됩니다.
- 본 저장소의 `web_portal/`에는 GitHub Actions를 통해 GitHub Pages로 즉시 배포되어 웹 브라우저에서 바로 열람할 수 있는 정적 웹 버전이 함께 구성되어 있습니다.
- 따라서 포트폴리오 면접관이나 방문자는 별도의 설치 없이도 온라인 URL만으로 시스템 UI와 관제 기능을 바로 확인해볼 수 있습니다!
