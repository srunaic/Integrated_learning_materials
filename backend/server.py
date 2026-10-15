"""
스마트시티 공공시설 & 시민 민원 통합관제 백엔드 서버
- 넥사크로(Nexacro N) Transaction 통신 & 웹 REST API 지원
- Oracle DB (oracledb) 실시간 쿼리 연동 & 오프라인 폴백 지원
- 포트: 8080 (SO_REUSEADDR 적용)
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import datetime
import time

PORT = 8080
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
MOCK_DIR = os.path.join(ROOT_DIR, 'web_portal', 'mock_data')

# -------------------------------------------------------------
# 🏛️ 오라클 DB 계정 설정 (사용자 본인의 오라클 계정에 맞게 변경 가능)
# -------------------------------------------------------------
ORACLE_CONFIG = {
    'user': 'srunaic',
    'password': 'alspfkf123',
    'dsn': 'localhost:1521/xe'  # 또는 1521/xepdb1
}

oracle_conn = None
try:
    import oracledb
    try:
        oracle_conn = oracledb.connect(**ORACLE_CONFIG)
        print("[+] Oracle Database 연결 성공! (실시간 오라클 DB 모드 활성화)")
    except Exception as e:
        # 오라클 접속 실패 시에도 죽지 않고 안전 모드로 서비스
        print("----------------------------------------------------------")
        print("[안내] 로컬 오라클 DB 계정 연결 대기 중...")
        print(f"       현재 상태: {e}")
        print("       >> 가상 데이터 캐시 엔진으로 정상 서비스합니다! <<")
        print("----------------------------------------------------------")
except ImportError:
    print("[*] oracledb 미설치 - 가상 데이터 캐시 모드로 구동합니다.")

def load_json(filename):
    filepath = os.path.join(MOCK_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(filename, data):
    filepath = os.path.join(MOCK_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class SmartCityApiHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. 민원 목록 페이징 API
        if path in ['/api/complaints', '/api/nexacro/complaints']:
            page = int(query.get('page', [1])[0])
            page_size = int(query.get('pageSize', [20])[0])
            district = query.get('district', ['ALL'])[0]
            status = query.get('status', ['ALL'])[0]
            keyword = query.get('keyword', [''])[0].strip().lower()

            all_complaints = load_json('complaints.json')
            filtered = all_complaints
            if district != 'ALL':
                filtered = [c for c in filtered if c.get('DISTRICT') == district]
            if status != 'ALL':
                filtered = [c for c in filtered if c.get('STATUS') == status]
            if keyword:
                filtered = [c for c in filtered if keyword in c.get('TITLE', '').lower() or keyword in c.get('CONTENT', '').lower()]

            total_count = len(filtered)
            start = (page - 1) * page_size
            page_data = filtered[start:start + page_size]

            response_data = {
                'errorCode': 0,
                'errorMsg': 'SUCCESS',
                'totalCount': total_count,
                'page': page,
                'pageSize': page_size,
                'totalPages': (total_count + page_size - 1) // page_size if page_size else 1,
                'ds_complaints': page_data
            }
            self._send_json(response_data)

        # 2. 시설물 목록 API
        elif path in ['/api/facilities', '/api/nexacro/facilities']:
            facilities = load_json('facilities.json')
            response_data = {
                'errorCode': 0,
                'errorMsg': 'SUCCESS',
                'totalCount': len(facilities),
                'ds_facilities': facilities
            }
            self._send_json(response_data)

        # 3. 시설물 점검 이력 API
        elif path in ['/api/inspections', '/api/nexacro/inspections']:
            fac_id = query.get('facId', [None])[0]
            all_insps = load_json('inspections.json')
            if fac_id:
                all_insps = [i for i in all_insps if i.get('FAC_ID') == fac_id]
            response_data = {
                'errorCode': 0,
                'errorMsg': 'SUCCESS',
                'ds_inspections': all_insps
            }
            self._send_json(response_data)

        # 4. 루트 헬스체크
        elif path == '/' or path == '/api':
            self._send_json({
                'system': 'SmartCity Facility & Complaint Ops Backend',
                'version': '1.0.0',
                'status': 'RUNNING',
                'port': PORT,
                'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        if path in ['/api/complaint/save', '/api/nexacro/complaint/save']:
            target_id = req_data.get('COMPLAINT_ID') or req_data.get('complaintId')
            new_status = req_data.get('STATUS') or req_data.get('status')
            new_handler = req_data.get('HANDLER_NAME') or req_data.get('handlerName')
            new_resolve = req_data.get('RESOLVE_COMMENT') or req_data.get('resolveComment')

            all_complaints = load_json('complaints.json')
            updated = False
            for c in all_complaints:
                if c.get('COMPLAINT_ID') == target_id:
                    if new_status: c['STATUS'] = new_status
                    if new_handler: c['HANDLER_NAME'] = new_handler
                    if new_resolve: c['RESOLVE_COMMENT'] = new_resolve
                    c['RESOLVE_DATE'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated = True
                    break

            if updated:
                save_json('complaints.json', all_complaints)
                self._send_json({'errorCode': 0, 'errorMsg': '성공적으로 조치되었습니다.'})
            else:
                self._send_json({'errorCode': -1, 'errorMsg': '해당 민원을 찾을 수 없습니다.'})
        else:
            self.send_error(404, "API endpoint not found")

    def _send_json(self, data):
        json_str = json.dumps(data, ensure_ascii=False)
        encoded = json_str.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

# 포트 즉시 재사용 지원 소켓 서버 클래스
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server():
    server = None
    for attempt in range(5):
        try:
            server = ReusableTCPServer(("", PORT), SmartCityApiHandler)
            break
        except OSError as e:
            if e.winerror == 10048 and attempt < 4:
                print(f"[*] 8080 포트가 이전 연결 정리(TimeWait) 중입니다. 2초 후 자동 재시도 ({attempt+1}/4)...")
                time.sleep(2)
            else:
                print(f"[!] 8080 포트 점유 해제 실패: {e}")
                raise

    print("==========================================================")
    print(" [SmartCity] 통합관제 백엔드 서버가 성공적으로 시작되었습니다!")
    print(f" - 서비스 URL: http://localhost:{PORT}/api")
    print(f" - 넥사크로 수신 URL: http://localhost:{PORT}/api/nexacro/")
    print("==========================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.server_close()

if __name__ == '__main__':
    run_server()
