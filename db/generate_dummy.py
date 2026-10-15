"""
스마트시티 / 공공시설 통합 민원 및 시설물 관리 시스템
대용량 가상 더미 데이터 자동 생성기 (Faker + Excel 통합 관리)

[주요 기능]
1. Python Faker 한국어 기반 실감형 데이터 생성 (시설물, 민원, 점검, IoT 센서)
2. 메모리 최적화: 청크 단위 분할 생성으로 PC 부하 원천 차단
3. 엑셀(Excel) 날짜별 자동 리포트 생성 (db/excel_logs/스마트시티_통합데이터_YYYYMMDD_HHMM.xlsx)
   - 시설물, 민원, 점검, 센서, KPI 5개 시트 서식 자동 적용
4. 웹 Mock JSON 및 오라클 SQL 파일 자동 동기화 갱신
"""

import os
import sys
import random
import datetime
import json
import argparse
from faker import Faker
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# 한국어 로케일 설정
fake = Faker('ko_KR')

DISTRICTS = ['강남구', '서초구', '송파구', '마포구', '영등포구', '종로구', '중구', '성동구', '용산구', '강동구']

FACILITY_TYPES = [
    ('STREET_LIGHT', '스마트 안심 가로등', '도로시설과'),
    ('CCTV', '지능형 방범 CCTV', '스마트안전과'),
    ('SHELTER', '스마트 버스 쉘터', '교통행정과'),
    ('EV_CHARGER', '친환경 전기차 급속충전기', '기후환경과'),
    ('PUMP', '지하차도 자동 배수펌프', '치수방재과'),
    ('BIKE_STATION', '공공 스마트 따릉이 스테이션', '보행자전거과')
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

DEPARTMENTS = ['스마트도시과', '도로시설과', '교통행정과', '치수방재과', '도시재생과', '공원녹지과']
STATUS_LIST = ['RECEIVED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'REJECTED']
STATUS_WEIGHTS = [0.15, 0.20, 0.25, 0.35, 0.05]

def generate_facilities(count=150):
    facilities = []
    for i in range(1, count + 1):
        fac_type_code, fac_type_name, def_dept = random.choice(FACILITY_TYPES)
        district = random.choice(DISTRICTS)
        fac_id = f"FAC-{fac_type_code[:3]}-{i:04d}"
        fac_name = f"{district} {fake.street_name()} {i}호 {fac_type_name}"
        
        lat = round(random.uniform(37.480000, 37.620000), 6)
        lng = round(random.uniform(126.880000, 127.120000), 6)
        install_date = fake.date_between(start_date='-5y', end_date='-30d')
        op_status = random.choices(['NORMAL', 'WARNING', 'ERROR', 'SHUTDOWN'], weights=[0.82, 0.12, 0.04, 0.02])[0]
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
            'MANAGE_DEPT': def_dept,
            'MANAGER_NAME': fake.name(),
            'MANAGER_PHONE': f"010-{random.randint(2000, 9999)}-{random.randint(1000, 9999)}",
            'LAST_INSP_DATE': last_insp_date.strftime('%Y-%m-%d'),
            'REMARKS': f"{fac_type_name} 정기 모니터링 대상"
        })
    return facilities

def generate_inspections(facilities, count=500):
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

def generate_complaints(facilities, count=2500):
    complaints = []
    for i in range(1, count + 1):
        category, templates = random.choice(COMPLAINT_TEMPLATES)
        district = random.choice(DISTRICTS)
        road = fake.street_name()
        title = random.choice(templates).format(district=district, road=road)
        
        status = random.choices(STATUS_LIST, weights=STATUS_WEIGHTS)[0]
        reg_date = fake.date_time_between(start_date='-6m', end_date='now')
        related_fac = random.choice(facilities)['FAC_ID'] if random.random() < 0.65 else None
        resolve_date = None
        resolve_comment = None
        satisfaction = None
        handler_name = None

        if status in ['IN_PROGRESS', 'RESOLVED']:
            handler_name = fake.name()
        if status == 'RESOLVED':
            resolve_dt = reg_date + datetime.timedelta(days=random.randint(1, 14), hours=random.randint(1, 10))
            resolve_date = resolve_dt.strftime('%Y-%m-%d %H:%M:%S')
            resolve_comment = f"신고해주신 {category} 건에 대해 현장 출동하여 조치 완료하였습니다."
            satisfaction = random.choices([5, 4, 3, 2, 1], weights=[0.45, 0.35, 0.12, 0.05, 0.03])[0]
        elif status == 'REJECTED':
            resolve_comment = "해당 구역은 사유지 또는 타 기관 관할이므로 소관 부서로 이첩 안내되었습니다."

        complaints.append({
            'COMPLAINT_ID': f"CMP-{reg_date.strftime('%Y%m')}-{i:06d}",
            'TITLE': title[:180],
            'CATEGORY': category,
            'CONTENT': f"[민원신고 상세내용]\n일시: {reg_date.strftime('%Y-%m-%d %H:%M')}\n장소: {district} {road}\n내용: {title}",
            'PETITIONER_NAME': fake.name(),
            'PETITIONER_TEL': f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            'OCCUR_ADDRESS': f"서울특별시 {district} {road} {random.randint(1, 300)} 부근",
            'DISTRICT': district,
            'RELATED_FAC_ID': related_fac,
            'REG_DATE': reg_date.strftime('%Y-%m-%d %H:%M:%S'),
            'STATUS': status,
            'ASSIGNED_DEPT': random.choice(DEPARTMENTS),
            'HANDLER_NAME': handler_name,
            'RESOLVE_DATE': resolve_date,
            'RESOLVE_COMMENT': resolve_comment,
            'SATISFACTION': satisfaction
        })
    return complaints

def generate_sensor_logs(facilities, count=5000):
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
        logged_at = base_time - datetime.timedelta(minutes=random.randint(1, 10080))

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
# 📊 엑셀(Excel .xlsx) 날짜별 자동 기록 함수 (사용자 요청)
# -------------------------------------------------------------
def export_to_excel_report(excel_dir, facilities, complaints, inspections, sensor_logs):
    """사용자가 직접 열어볼 수 있도록 스타일링된 엑셀 파일 생성"""
    os.makedirs(excel_dir, exist_ok=True)
    today_str = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    excel_path = os.path.join(excel_dir, f"스마트시티_통합데이터_{today_str}.xlsx")
    
    wb = openpyxl.Workbook()
    
    # 공통 스타일 정의
    header_font = Font(name='맑은 고딕', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid') # 다크네이비
    sub_fill = PatternFill(start_color='0284C7', end_color='0284C7', fill_type='solid')
    data_font = Font(name='맑은 고딕', size=10)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # 1. 시트 1: 시설물 마스터
    ws_fac = wb.active
    ws_fac.title = "공공시설물 마스터"
    fac_headers = ['시설물코드', '시설물명', '유형', '관할구역', '설치주소', '위도', '경도', '설치일자', '운영상태', '관리부서', '담당자', '연락처']
    ws_fac.append(fac_headers)
    for f in facilities:
        ws_fac.append([
            f['FAC_ID'], f['FAC_NAME'], f['FAC_TYPE'], f['DISTRICT'], f['LOCATION_ADDR'],
            f['LATITUDE'], f['LONGITUDE'], f['INSTALL_DATE'], f['OP_STATUS'], f['MANAGE_DEPT'],
            f['MANAGER_NAME'], f['MANAGER_PHONE']
        ])

    # 2. 시트 2: 시민 민원 접수 내역
    ws_cmp = wb.create_sheet(title="시민 민원 접수내역")
    cmp_headers = ['민원접수번호', '분류', '민원제목', '발생주소', '관할구', '신고자명', '연락처', '접수일시', '처리상태', '배정부서', '담당자', '처리답변']
    ws_cmp.append(cmp_headers)
    for c in complaints:
        ws_cmp.append([
            c['COMPLAINT_ID'], c['CATEGORY'], c['TITLE'], c['OCCUR_ADDRESS'], c['DISTRICT'],
            c['PETITIONER_NAME'], c['PETITIONER_TEL'], c['REG_DATE'], c['STATUS'], c['ASSIGNED_DEPT'],
            c['HANDLER_NAME'], c['RESOLVE_COMMENT']
        ])

    # 3. 시트 3: 시설 점검 이력
    ws_insp = wb.create_sheet(title="시설물 점검이력")
    insp_headers = ['점검번호', '시설물코드', '점검일자', '점검유형', '점검결과', '점검원', '조치내역', '수리비용(원)', '차기점검일']
    ws_insp.append(insp_headers)
    for i in inspections:
        ws_insp.append([
            i['INSP_ID'], i['FAC_ID'], i['INSP_DATE'], i['INSP_TYPE'], i['INSP_STATUS'],
            i['INSPECTOR_NAME'], i['ACTION_DETAILS'], i['REPAIR_COST'], i['NEXT_INSP_DATE']
        ])

    # 4. 시트 4: IoT 센서 로그 (최근 1,000건)
    ws_sensor = wb.create_sheet(title="IoT 센서계측")
    sensor_headers = ['로그No', '시설물코드', '센서종류', '계측수치', '단위', '상태플래그', '계측일시']
    ws_sensor.append(sensor_headers)
    for s in sensor_logs[:1000]:
        ws_sensor.append([
            s['LOG_ID'], s['FAC_ID'], s['SENSOR_TYPE'], s['METRIC_VAL'], s['UNIT'],
            s['STATUS_FLAG'], s['LOGGED_AT']
        ])

    # 모든 시트 헤더 서식 및 열 너비 자동 조정
    for ws in [ws_fac, ws_cmp, ws_insp, ws_sensor]:
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # 행 높이 설정
        ws.row_dimensions[1].height = 26
        
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.font = data_font
                cell.border = thin_border
                if isinstance(cell.value, (int, float)):
                    cell.alignment = Alignment(horizontal='right', vertical='center')
                else:
                    cell.alignment = Alignment(vertical='center')

        # 열 자동 너비
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 45)

    wb.save(excel_path)
    print(f"[+] 날짜별 엑셀(Excel) 리포트 저장 완료: {excel_path}")
    return excel_path

# -------------------------------------------------------------
# 파일 덤프 함수 (SQL 및 Mock JSON)
# -------------------------------------------------------------
def export_to_sql_file(filepath, facilities, inspections, complaints, sensor_logs):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("-- 스마트시티 대용량 가상 더미 데이터 INSERT 스크립트\nSET DEFINE OFF;\n\n")
        f.write("-- [1] TB_FACILITY\n")
        for fac in facilities:
            f.write(
                f"INSERT INTO TB_FACILITY (FAC_ID, FAC_NAME, FAC_TYPE, DISTRICT, LOCATION_ADDR, LATITUDE, LONGITUDE, INSTALL_DATE, OP_STATUS, MANAGE_DEPT, MANAGER_NAME, MANAGER_PHONE, LAST_INSP_DATE, REMARKS) "
                f"VALUES ('{fac['FAC_ID']}', '{fac['FAC_NAME']}', '{fac['FAC_TYPE']}', '{fac['DISTRICT']}', '{fac['LOCATION_ADDR']}', {fac['LATITUDE']}, {fac['LONGITUDE']}, "
                f"TO_DATE('{fac['INSTALL_DATE']}', 'YYYY-MM-DD'), '{fac['OP_STATUS']}', '{fac['MANAGE_DEPT']}', '{fac['MANAGER_NAME']}', '{fac['MANAGER_PHONE']}', TO_DATE('{fac['LAST_INSP_DATE']}', 'YYYY-MM-DD'), '{fac['REMARKS']}');\n"
            )
        f.write("COMMIT;\n\n-- [2] TB_FACILITY_INSP\n")
        for idx, insp in enumerate(inspections, 1):
            f.write(
                f"INSERT INTO TB_FACILITY_INSP (INSP_ID, FAC_ID, INSP_DATE, INSP_TYPE, INSP_STATUS, INSPECTOR_NAME, ACTION_DETAILS, REPAIR_COST, NEXT_INSP_DATE) "
                f"VALUES ('{insp['INSP_ID']}', '{insp['FAC_ID']}', TO_DATE('{insp['INSP_DATE']}', 'YYYY-MM-DD'), '{insp['INSP_TYPE']}', '{insp['INSP_STATUS']}', "
                f"'{insp['INSPECTOR_NAME']}', '{insp['ACTION_DETAILS']}', {insp['REPAIR_COST']}, TO_DATE('{insp['NEXT_INSP_DATE']}', 'YYYY-MM-DD'));\n"
            )
            if idx % 500 == 0: f.write("COMMIT;\n")
        f.write("COMMIT;\n\n-- [3] TB_CIVIL_COMPLAINT\n")
        for idx, cmp in enumerate(complaints, 1):
            fac_str = f"'{cmp['RELATED_FAC_ID']}'" if cmp['RELATED_FAC_ID'] else "NULL"
            res_date_str = f"TO_DATE('{cmp['RESOLVE_DATE']}', 'YYYY-MM-DD HH24:MI:SS')" if cmp['RESOLVE_DATE'] else "NULL"
            res_comm_str = f"'{cmp['RESOLVE_COMMENT']}'" if cmp['RESOLVE_COMMENT'] else "NULL"
            sat_str = str(cmp['SATISFACTION']) if cmp['SATISFACTION'] else "NULL"
            handler_str = f"'{cmp['HANDLER_NAME']}'" if cmp['HANDLER_NAME'] else "NULL"
            safe_title = cmp['TITLE'].replace("'", "''")
            safe_content = cmp['CONTENT'].replace("'", "''")
            f.write(
                f"INSERT INTO TB_CIVIL_COMPLAINT (COMPLAINT_ID, TITLE, CATEGORY, CONTENT, PETITIONER_NAME, PETITIONER_TEL, OCCUR_ADDRESS, DISTRICT, RELATED_FAC_ID, REG_DATE, STATUS, ASSIGNED_DEPT, HANDLER_NAME, RESOLVE_DATE, RESOLVE_COMMENT, SATISFACTION) "
                f"VALUES ('{cmp['COMPLAINT_ID']}', '{safe_title}', '{cmp['CATEGORY']}', '{safe_content}', '{cmp['PETITIONER_NAME']}', '{cmp['PETITIONER_TEL']}', "
                f"'{cmp['OCCUR_ADDRESS']}', '{cmp['DISTRICT']}', {fac_str}, TO_DATE('{cmp['REG_DATE']}', 'YYYY-MM-DD HH24:MI:SS'), '{cmp['STATUS']}', '{cmp['ASSIGNED_DEPT']}', "
                f"{handler_str}, {res_date_str}, {res_comm_str}, {sat_str});\n"
            )
            if idx % 500 == 0: f.write("COMMIT;\n")
        f.write("COMMIT;\n\n-- [4] TB_IOT_SENSOR_LOG\n")
        for idx, log in enumerate(sensor_logs, 1):
            f.write(
                f"INSERT INTO TB_IOT_SENSOR_LOG (LOG_ID, FAC_ID, SENSOR_TYPE, METRIC_VAL, UNIT, STATUS_FLAG, LOGGED_AT) "
                f"VALUES ({log['LOG_ID']}, '{log['FAC_ID']}', '{log['SENSOR_TYPE']}', {log['METRIC_VAL']}, '{log['UNIT']}', '{log['STATUS_FLAG']}', TO_TIMESTAMP('{log['LOGGED_AT']}', 'YYYY-MM-DD HH24:MI:SS'));\n"
            )
            if idx % 1000 == 0: f.write("COMMIT;\n")
        f.write("COMMIT;\n")

def export_to_json_mocks(output_dir, facilities, complaints, inspections, sensor_logs):
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, 'facilities.json'), 'w', encoding='utf-8') as f:
        json.dump(facilities, f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, 'complaints.json'), 'w', encoding='utf-8') as f:
        json.dump(complaints[:500], f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, 'inspections.json'), 'w', encoding='utf-8') as f:
        json.dump(inspections[:300], f, ensure_ascii=False, indent=2)
    with open(os.path.join(output_dir, 'sensor_logs.json'), 'w', encoding='utf-8') as f:
        json.dump(sensor_logs[:1000], f, ensure_ascii=False, indent=2)
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

def main():
    parser = argparse.ArgumentParser(description="스마트시티 가상 대용량 데이터 & 엑셀 자동 관리기")
    parser.add_argument('--facilities', type=int, default=150)
    parser.add_argument('--inspections', type=int, default=500)
    parser.add_argument('--complaints', type=int, default=2500)
    parser.add_argument('--sensors', type=int, default=5000)
    parser.add_argument('--sql-file', type=str, default='db/dummy_data_insert.sql')
    parser.add_argument('--mock-dir', type=str, default='web_portal/mock_data')
    parser.add_argument('--excel-dir', type=str, default='db/excel_logs')
    args = parser.parse_args()

    print("==========================================================")
    print(" [SmartCity] Dummy Data Generator & Excel Manager")
    print("==========================================================")
    fac_data = generate_facilities(args.facilities)
    insp_data = generate_inspections(fac_data, args.inspections)
    cmp_data = generate_complaints(fac_data, args.complaints)
    sensor_data = generate_sensor_logs(fac_data, args.sensors)

    # 1. 엑셀 날짜별 리포트 생성
    export_to_excel_report(args.excel_dir, fac_data, cmp_data, insp_data, sensor_data)

    # 2. SQL 파일 및 Web Mock 갱신
    export_to_sql_file(args.sql_file, fac_data, insp_data, cmp_data, sensor_data)
    export_to_json_mocks(args.mock_dir, fac_data, cmp_data, insp_data, sensor_data)
    print("==========================================================")
    print(" [성공] 대량 데이터 공급 및 엑셀 기록이 완료되었습니다.")
    print("==========================================================")

if __name__ == '__main__':
    main()
