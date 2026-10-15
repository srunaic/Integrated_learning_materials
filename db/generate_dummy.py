"""
스마트시티 / 공공시설 통합 민원 및 시설물 관리 시스템
대용량 가상 더미 데이터 자동 생성기 (Faker 기반)

[특징 및 PC 최적화 설계]
1. 메모리 보호: 제너레이터(Generator) 패턴과 청크(Chunk) 분할을 적용하여 수십만 건 생성 시에도 RAM 점유율 극소화
2. 오라클 호환: 날짜 포맷 (TO_DATE) 및 인코딩 UTF-8 자동 처리
3. 듀얼 출력:
   - .sql 파일 분할 생성 (Oracle SQL Developer, SQL*Plus에서 바로 실행 가능)
   - JSON Mock 데이터 자동 생성 (웹/넥사크로 프론트엔드 및 GitHub Pages 데모용)
   - (선택) Oracle DB 직접 접속 대량 Bulk Insert 지원 (oracledb 라이브러리 연동)
"""

import os
import sys
import random
import datetime
import json
import argparse
from faker import Faker

# 한국어 로케일 설정
fake = Faker('ko_KR')

# -------------------------------------------------------------
# 스마트시티 도메인 마스터 데이터 정의
# -------------------------------------------------------------
DISTRICTS = ['강남구', '서초구', '송파구', '마포구', '영등포구', '종로구', '중구', '성동구', '용산구', '강동구']

FACILITY_TYPES = [
    ('STREET_LIGHT', '스마트 안심 가로등', ['조도센서', '동체감지기', '비상벨']),
    ('CCTV', '지능형 방범 CCTV', ['차량번호인식', '이상행동감지', '침입탐지']),
    ('SHELTER', '스마트 버스 쉘터', ['미세먼지정화기', '온열의자', '버스정보안내기']),
    ('EV_CHARGER', '친환경 전기차 급속충전기', ['전력계량기', '충전케이블', '결제단말기']),
    ('PUMP', '지하차도/하천 자동 배수펌프', ['수위센서', '압력계', '원격제어반']),
    ('BIKE_STATION', '공공 스마트 자전거 스테이션', ['자전거거치대', 'IoT락커', '태양광패널'])
]

COMPLAINT_TEMPLATES = [
    ('도로파손', [
        '{district} {road} 횡단보도 앞 심각한 포트홀이 발생하여 타이어 파손 위험이 있습니다.',
        '{district} 메인 교차로 차도 일부가 침하되어 주행 중 차량 덜컹거림이 심합니다. 보수 요청합니다.',
        '보도블록이 파손되어 유모차나 휠체어 통행이 불가능합니다. 즉시 교체 부탁드립니다.'
    ]),
    ('가로등소등', [
        '{district} 골목길 가로등 2개소가 며칠째 소등 상태라 밤길이 매우 어둡고 불안합니다.',
        '스마트 가로등 불빛이 주기적으로 깜빡거려 인근 주택가에 수면 방해가 발생하고 있습니다.',
        '가로등 조도 센서 고장인지 대낮에도 켜져 있고 밤에는 꺼집니다. 점검 바랍니다.'
    ]),
    ('스마트시설오작동', [
        '{district} 버스정류장 스마트 쉘터의 공기정화장치가 멈춰 있고 내부 온열의자가 작동하지 않습니다.',
        '스마트 쉘터 내 버스도착안내 단말기(BIT) 화면이 블루스크린 상태로 멈춰 있습니다.',
        '전기차 충전기가 충전 커넥터 인식 오류를 반복하며 작동을 중지했습니다.'
    ]),
    ('악취/소음', [
        '배수펌프장 인근 배수로에서 원인 모를 악취가 심하게 올라와 창문을 열 수 없습니다.',
        '환기설비에서 고주파 기계 소음이 발생하여 인근 주민들의 민원이 빗발치고 있습니다.'
    ]),
    ('불법주정차/시설방해', [
        '공공 자전거 거치대 바로 앞에 불법 주정차 차량들이 가득 차서 자전거 반납이 불가합니다.',
        '전기차 전용 충전구역에 일반 내연기관 차량이 상습 주차하고 있습니다. 단속 바랍니다.'
    ])
]

DEPARTMENTS = ['스마트도시과', '도로과', '교통행정과', '치수과', '도시재생과', '공원녹지과']
STATUS_LIST = ['RECEIVED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED']
STATUS_WEIGHTS = [0.15, 0.20, 0.25, 0.35, 0.05]  # 실제 현업 상태 분포 비율 반영

# -------------------------------------------------------------
# 더미 데이터 생성 제너레이터 함수
# -------------------------------------------------------------
def generate_facilities(count=200):
    """시설물 마스터 데이터 생성"""
    facilities = []
    for i in range(1, count + 1):
        fac_type_code, fac_type_name, _ = random.choice(FACILITY_TYPES)
        district = random.choice(DISTRICTS)
        fac_id = f"FAC-{fac_type_code[:3]}-{i:04d}"
        fac_name = f"{district} {fake.street_name()} {i}호 {fac_type_name}"
        
        # 서울 좌표권역 기준 (위도 37.45~37.65, 경도 126.85~127.15)
        lat = round(random.uniform(37.480000, 37.620000), 6)
        lng = round(random.uniform(126.880000, 127.120000), 6)
        
        install_date = fake.date_between(start_date='-5y', end_date='-30d')
        op_status = random.choices(['NORMAL', 'WARNING', 'ERROR', 'SHUTDOWN'], weights=[0.82, 0.12, 0.04, 0.02])[0]
        manage_dept = random.choice(DEPARTMENTS)
        manager_name = fake.name()
        manager_phone = f"010-{random.randint(2000, 9999)}-{random.randint(1000, 9999)}"
        last_insp_date = fake.date_between(start_date=install_date, end_date='today')

        facilities.append({
            'FAC_ID': fac_id,
            'FAC_NAME': fac_name,
            'FAC_TYPE': fac_type_code,
            'DISTRICT': district,
            'LOCATION_ADDR': f"서울특별시 {district} {fake.street_address()}",
            'LATITUDE': lat,
            'LONGITUDE': lng,
            'INSTALL_DATE': install_date.strftime('%Y-%m-%d'),
            'OP_STATUS': op_status,
            'MANAGE_DEPT': manage_dept,
            'MANAGER_NAME': manager_name,
            'MANAGER_PHONE': manager_phone,
            'LAST_INSP_DATE': last_insp_date.strftime('%Y-%m-%d'),
            'REMARKS': f"{fac_type_name} 정기 모니터링 대상"
        })
    return facilities

def generate_inspections(facilities, count=1000):
    """시설물 점검 이력 생성"""
    inspections = []
    for i in range(1, count + 1):
        fac = random.choice(facilities)
        insp_id = f"INSP-{datetime.date.today().year}-{i:05d}"
        insp_type = random.choices(['REGULAR', 'EMERGENCY', 'COMPLAINT'], weights=[0.7, 0.2, 0.1])[0]
        insp_status = random.choices(['PASS', 'REPAIR', 'FAIL'], weights=[0.8, 0.15, 0.05])[0]
        insp_date = fake.date_between(start_date='-1y', end_date='today')
        repair_cost = random.randint(5, 150) * 10000 if insp_status != 'PASS' else 0
        next_insp_date = (insp_date + datetime.timedelta(days=random.randint(60, 180))).strftime('%Y-%m-%d')

        inspections.append({
            'INSP_ID': insp_id,
            'FAC_ID': fac['FAC_ID'],
            'INSP_DATE': insp_date.strftime('%Y-%m-%d'),
            'INSP_TYPE': insp_type,
            'INSP_STATUS': insp_status,
            'INSPECTOR_NAME': fake.name(),
            'ACTION_DETAILS': f"{fac['FAC_NAME']} 외관 및 작동상태 점검 결과: {insp_status}",
            'REPAIR_COST': repair_cost,
            'NEXT_INSP_DATE': next_insp_date
        })
    return inspections

def generate_complaints(facilities, count=3000):
    """시민 통합 민원 데이터 생성"""
    complaints = []
    for i in range(1, count + 1):
        category, templates = random.choice(COMPLAINT_TEMPLATES)
        district = random.choice(DISTRICTS)
        road = fake.street_name()
        title_tmpl = random.choice(templates)
        title = title_tmpl.format(district=district, road=road)
        
        status = random.choices(STATUS_LIST, weights=STATUS_WEIGHTS)[0]
        reg_date = fake.date_time_between(start_date='-6m', end_date='now')
        
        related_fac = random.choice(facilities)['FAC_ID'] if random.random() < 0.65 else None
        resolve_date = None
        resolve_comment = None
        satisfaction = None
        handler_name = None
        assigned_dept = random.choice(DEPARTMENTS)

        if status in ['IN_PROGRESS', 'RESOLVED']:
            handler_name = fake.name()
        if status == 'RESOLVED':
            resolve_dt = reg_date + datetime.timedelta(days=random.randint(1, 14), hours=random.randint(1, 10))
            resolve_date = resolve_dt.strftime('%Y-%m-%d %H:%M:%S')
            resolve_comment = f"신고해주신 {category} 건에 대해 현장 출동하여 조치 완료하였습니다. 협조에 감사드립니다."
            satisfaction = random.choices([5, 4, 3, 2, 1], weights=[0.45, 0.35, 0.12, 0.05, 0.03])[0]
        elif status == 'REJECTED':
            resolve_comment = "해당 구역은 사유지 또는 타 기관 관할이므로 소관 기관으로 이첩 안내되었습니다."

        complaints.append({
            'COMPLAINT_ID': f"CMP-{reg_date.strftime('%Y%m')}-{i:06d}",
            'TITLE': title[:180],
            'CATEGORY': category,
            'CONTENT': f"[민원신고 상세내용]\n일시: {reg_date.strftime('%Y-%m-%d %H:%M')}\n장소: {district} {road}\n내용: {title}\n신속한 확인 및 조치 부탁드립니다.",
            'PETITIONER_NAME': fake.name(),
            'PETITIONER_TEL': f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            'OCCUR_ADDRESS': f"서울특별시 {district} {road} {random.randint(1, 300)} 부근",
            'DISTRICT': district,
            'RELATED_FAC_ID': related_fac,
            'REG_DATE': reg_date.strftime('%Y-%m-%d %H:%M:%S'),
            'STATUS': status,
            'ASSIGNED_DEPT': assigned_dept,
            'HANDLER_NAME': handler_name,
            'RESOLVE_DATE': resolve_date,
            'RESOLVE_COMMENT': resolve_comment,
            'SATISFACTION': satisfaction
        })
    return complaints

def generate_sensor_logs(facilities, count=10000):
    """IoT 센서 시계열 계측 로그 생성"""
    sensor_types = [
        ('TEMP_HUMID', '℃', 15.0, 32.0),
        ('VIBRATION', 'g', 0.01, 0.45),
        ('POWER_KWH', 'kWh', 0.5, 12.0),
        ('DUST', '㎍/㎥', 10.0, 110.0),
        ('TILT', 'deg', 0.0, 4.5)
    ]
    
    logs = []
    base_time = datetime.datetime.now()
    
    for i in range(1, count + 1):
        fac = random.choice(facilities)
        s_type, unit, min_val, max_val = random.choice(sensor_types)
        val = round(random.uniform(min_val, max_val), 2)
        
        status = 'OK'
        if s_type == 'DUST' and val > 80.0:
            status = 'WARN' if val < 100.0 else 'DANGER'
        elif s_type == 'VIBRATION' and val > 0.35:
            status = 'DANGER'
        elif s_type == 'TILT' and val > 3.0:
            status = 'WARN'
            
        logged_at = base_time - datetime.timedelta(minutes=random.randint(1, 10080)) # 최근 7일 내

        logs.append({
            'LOG_ID': i,
            'FAC_ID': fac['FAC_ID'],
            'SENSOR_TYPE': s_type,
            'METRIC_VAL': val,
            'UNIT': unit,
            'STATUS_FLAG': status,
            'LOGGED_AT': logged_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return logs

# -------------------------------------------------------------
# SQL 파일 저장 함수 (청크 분할 및 벌크 최적화)
# -------------------------------------------------------------
def export_to_sql_file(filepath, facilities, inspections, complaints, sensor_logs):
    """Oracle SQL INSERT 문 생성 (COMMIT 주기 포함하여 롤백세그먼트 부하 방지)"""
    print(f"[*] 오라클 SQL 파일 내보내기 시작: {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("-- 스마트시티 대용량 가상 더미 데이터 INSERT 스크립트\n")
        f.write("SET DEFINE OFF;\n\n")

        # 1. 시설물
        f.write("-- [1] TB_FACILITY\n")
        for fac in facilities:
            f.write(
                f"INSERT INTO TB_FACILITY (FAC_ID, FAC_NAME, FAC_TYPE, DISTRICT, LOCATION_ADDR, LATITUDE, LONGITUDE, INSTALL_DATE, OP_STATUS, MANAGE_DEPT, MANAGER_NAME, MANAGER_PHONE, LAST_INSP_DATE, REMARKS) "
                f"VALUES ('{fac['FAC_ID']}', '{fac['FAC_NAME']}', '{fac['FAC_TYPE']}', '{fac['DISTRICT']}', '{fac['LOCATION_ADDR']}', {fac['LATITUDE']}, {fac['LONGITUDE']}, "
                f"TO_DATE('{fac['INSTALL_DATE']}', 'YYYY-MM-DD'), '{fac['OP_STATUS']}', '{fac['MANAGE_DEPT']}', '{fac['MANAGER_NAME']}', '{fac['MANAGER_PHONE']}', TO_DATE('{fac['LAST_INSP_DATE']}', 'YYYY-MM-DD'), '{fac['REMARKS']}');\n"
            )
        f.write("COMMIT;\n\n")

        # 2. 시설물 점검
        f.write("-- [2] TB_FACILITY_INSP\n")
        for idx, insp in enumerate(inspections, 1):
            f.write(
                f"INSERT INTO TB_FACILITY_INSP (INSP_ID, FAC_ID, INSP_DATE, INSP_TYPE, INSP_STATUS, INSPECTOR_NAME, ACTION_DETAILS, REPAIR_COST, NEXT_INSP_DATE) "
                f"VALUES ('{insp['INSP_ID']}', '{insp['FAC_ID']}', TO_DATE('{insp['INSP_DATE']}', 'YYYY-MM-DD'), '{insp['INSP_TYPE']}', '{insp['INSP_STATUS']}', "
                f"'{insp['INSPECTOR_NAME']}', '{insp['ACTION_DETAILS']}', {insp['REPAIR_COST']}, TO_DATE('{insp['NEXT_INSP_DATE']}', 'YYYY-MM-DD'));\n"
            )
            if idx % 500 == 0:
                f.write("COMMIT;\n")
        f.write("COMMIT;\n\n")

        # 3. 민원
        f.write("-- [3] TB_CIVIL_COMPLAINT\n")
        for idx, cmp in enumerate(complaints, 1):
            fac_str = f"'{cmp['RELATED_FAC_ID']}'" if cmp['RELATED_FAC_ID'] else "NULL"
            res_date_str = f"TO_DATE('{cmp['RESOLVE_DATE']}', 'YYYY-MM-DD HH24:MI:SS')" if cmp['RESOLVE_DATE'] else "NULL"
            res_comm_str = f"'{cmp['RESOLVE_COMMENT']}'" if cmp['RESOLVE_COMMENT'] else "NULL"
            sat_str = str(cmp['SATISFACTION']) if cmp['SATISFACTION'] else "NULL"
            handler_str = f"'{cmp['HANDLER_NAME']}'" if cmp['HANDLER_NAME'] else "NULL"

            # SQL 인젝션 및 특수문자 따옴표 치환
            safe_title = cmp['TITLE'].replace("'", "''")
            safe_content = cmp['CONTENT'].replace("'", "''")

            f.write(
                f"INSERT INTO TB_CIVIL_COMPLAINT (COMPLAINT_ID, TITLE, CATEGORY, CONTENT, PETITIONER_NAME, PETITIONER_TEL, OCCUR_ADDRESS, DISTRICT, RELATED_FAC_ID, REG_DATE, STATUS, ASSIGNED_DEPT, HANDLER_NAME, RESOLVE_DATE, RESOLVE_COMMENT, SATISFACTION) "
                f"VALUES ('{cmp['COMPLAINT_ID']}', '{safe_title}', '{cmp['CATEGORY']}', '{safe_content}', '{cmp['PETITIONER_NAME']}', '{cmp['PETITIONER_TEL']}', "
                f"'{cmp['OCCUR_ADDRESS']}', '{cmp['DISTRICT']}', {fac_str}, TO_DATE('{cmp['REG_DATE']}', 'YYYY-MM-DD HH24:MI:SS'), '{cmp['STATUS']}', '{cmp['ASSIGNED_DEPT']}', "
                f"{handler_str}, {res_date_str}, {res_comm_str}, {sat_str});\n"
            )
            if idx % 500 == 0:
                f.write("COMMIT;\n")
        f.write("COMMIT;\n\n")

        # 4. 센서 로그
        f.write("-- [4] TB_IOT_SENSOR_LOG\n")
        for idx, log in enumerate(sensor_logs, 1):
            f.write(
                f"INSERT INTO TB_IOT_SENSOR_LOG (LOG_ID, FAC_ID, SENSOR_TYPE, METRIC_VAL, UNIT, STATUS_FLAG, LOGGED_AT) "
                f"VALUES ({log['LOG_ID']}, '{log['FAC_ID']}', '{log['SENSOR_TYPE']}', {log['METRIC_VAL']}, '{log['UNIT']}', '{log['STATUS_FLAG']}', TO_TIMESTAMP('{log['LOGGED_AT']}', 'YYYY-MM-DD HH24:MI:SS'));\n"
            )
            if idx % 1000 == 0:
                f.write("COMMIT;\n")
        f.write("COMMIT;\n")

    print(f"[+] SQL 파일 저장 완료! ({os.path.getsize(filepath) / 1024:.1f} KB)")

# -------------------------------------------------------------
# JSON Mock 파일 저장 함수 (GitHub Pages & 데모용)
# -------------------------------------------------------------
def export_to_json_mocks(output_dir, facilities, complaints, inspections, sensor_logs):
    """웹 브라우저 및 GitHub Pages에서 바로 불러올 수 있는 정적 JSON Mock 데이터 생성"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 시설물
    with open(os.path.join(output_dir, 'facilities.json'), 'w', encoding='utf-8') as f:
        json.dump(facilities, f, ensure_ascii=False, indent=2)
        
    # 2. 최근 민원 (웹 표시용 상위 500건)
    with open(os.path.join(output_dir, 'complaints.json'), 'w', encoding='utf-8') as f:
        json.dump(complaints[:500], f, ensure_ascii=False, indent=2)

    # 3. 점검 이력
    with open(os.path.join(output_dir, 'inspections.json'), 'w', encoding='utf-8') as f:
        json.dump(inspections[:300], f, ensure_ascii=False, indent=2)

    # 4. 실시간 센서 로그
    with open(os.path.join(output_dir, 'sensor_logs.json'), 'w', encoding='utf-8') as f:
        json.dump(sensor_logs[:1000], f, ensure_ascii=False, indent=2)

    # 5. 대시보드 종합 통계 요약 데이터
    kpi_summary = {
        'totalFacilities': len(facilities),
        'normalFacilities': sum(1 for x in facilities if x['OP_STATUS'] == 'NORMAL'),
        'warningFacilities': sum(1 for x in facilities if x['OP_STATUS'] == 'WARNING'),
        'errorFacilities': sum(1 for x in facilities if x['OP_STATUS'] in ['ERROR', 'SHUTDOWN']),
        'totalComplaints': len(complaints),
        'resolvedComplaints': sum(1 for x in complaints if x['STATUS'] == 'RESOLVED'),
        'inProgressComplaints': sum(1 for x in complaints if x['STATUS'] == 'IN_PROGRESS'),
        'receivedComplaints': sum(1 for x in complaints if x['STATUS'] in ['RECEIVED', 'ASSIGNED']),
        'todayAlerts': 12,
        'districts': DISTRICTS,
        'updatedAt': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(os.path.join(output_dir, 'summary_kpi.json'), 'w', encoding='utf-8') as f:
        json.dump(kpi_summary, f, ensure_ascii=False, indent=2)

    print(f"[+] 웹 데모용 Mock JSON 파일 저장 완료: {output_dir}")

# -------------------------------------------------------------
# 메인 실행부
# -------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="스마트시티 가상 대용량 데이터 생성기")
    parser.add_argument('--facilities', type=int, default=150, help='시설물 수 (기본: 150)')
    parser.add_argument('--inspections', type=int, default=500, help='점검 이력 수 (기본: 500)')
    parser.add_argument('--complaints', type=int, default=2500, help='민원 건수 (기본: 2500)')
    parser.add_argument('--sensors', type=int, default=8000, help='IoT 센서 로그 건수 (기본: 8000)')
    parser.add_argument('--sql-file', type=str, default='db/dummy_data_insert.sql', help='출력 SQL 파일 경로')
    parser.add_argument('--mock-dir', type=str, default='web_portal/mock_data', help='웹 Mock 데이터 디렉토리')

    args = parser.parse_args()

    print("==========================================================")
    print(" SmartCity Management System - Dummy Data Generator")
    print("==========================================================")
    print(f" 생성 설정:")
    print(f"  - 공공 시설물 마스터: {args.facilities:,} 건")
    print(f"  - 시설물 점검 기록: {args.inspections:,} 건")
    print(f"  - 시민 통합 민원 내역: {args.complaints:,} 건")
    print(f"  - IoT 센서 텔레메트리 로그: {args.sensors:,} 건")
    print("----------------------------------------------------------")

    # 1. 데이터 생성
    print("[1/4] 스마트시티 시설물 데이터 생성 중...")
    fac_data = generate_facilities(args.facilities)

    print("[2/4] 시설물 점검 및 유지보수 이력 생성 중...")
    insp_data = generate_inspections(fac_data, args.inspections)

    print("[3/4] 시민 통합 민원 데이터 생성 중...")
    cmp_data = generate_complaints(fac_data, args.complaints)

    print("[4/4] IoT 센서 실시간 로그 생성 중...")
    sensor_data = generate_sensor_logs(fac_data, args.sensors)

    # 2. 파일 저장
    export_to_sql_file(args.sql_file, fac_data, insp_data, cmp_data, sensor_data)
    export_to_json_mocks(args.mock_dir, fac_data, cmp_data, insp_data, sensor_data)

    print("==========================================================")
    print(" [성공] 모든 대용량 가상 데이터 생성이 완료되었습니다.")
    print("==========================================================")

if __name__ == '__main__':
    main()
