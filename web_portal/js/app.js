/**
 * SmartCity Nexacro Web Application Core Logic
 * - eGovFrame & Nexacro Grid/Form State Emulation
 * - GitHub Pages Mock Mode & Local REST API Dual Support
 */

const AppState = {
  activeTab: 'tab-dashboard',
  backendMode: 'MOCK', // 'MOCK' or 'LOCAL_EGOV'
  apiBaseUrl: 'http://localhost:8080/api',
  
  // Data Store (Nexacro Datasets)
  ds_facilities: [],
  ds_complaints: [],
  ds_inspections: [],
  ds_sensor_logs: [],
  summaryKpi: null,

  // Pagination & Filter for Complaints
  complaintPage: 1,
  pageSize: 15,
  filteredComplaints: [],
  selectedComplaint: null,

  // Facility filter
  selectedFacility: null
};

// -------------------------------------------------------------
// 초기화 및 이벤트 리스너 등록
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  initClock();
  initTabNavigation();
  initEventListeners();
  await loadData();
  renderDashboard();
  renderComplaintsTable();
  renderFacilitiesTable();
  renderSensorMonitoring();
});

// 시계 업데이트
function initClock() {
  const clockEl = document.getElementById('liveClock');
  const update = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleDateString('ko-KR', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit'
    });
  };
  update();
  setInterval(update, 1000);
}

// 탭 네비게이션
function initTabNavigation() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      
      btn.classList.add('active');
      const targetTab = btn.getAttribute('data-target');
      document.getElementById(targetTab).classList.add('active');
      AppState.activeTab = targetTab;
    });
  });
}

// -------------------------------------------------------------
// 데이터 로딩 (Dual Mode: Mock JSON vs Local eGovFrame)
// -------------------------------------------------------------
async function loadData() {
  const statusLabel = document.getElementById('modeLabel');
  try {
    // 1. Mock Data 로딩
    const [facRes, cmpRes, inspRes, sensorRes, kpiRes] = await Promise.all([
      fetch('mock_data/facilities.json').then(r => r.json()),
      fetch('mock_data/complaints.json').then(r => r.json()),
      fetch('mock_data/inspections.json').then(r => r.json()),
      fetch('mock_data/sensor_logs.json').then(r => r.json()),
      fetch('mock_data/summary_kpi.json').then(r => r.json())
    ]);

    AppState.ds_facilities = facRes;
    AppState.ds_complaints = cmpRes;
    AppState.ds_inspections = inspRes;
    AppState.ds_sensor_logs = sensorRes;
    AppState.summaryKpi = kpiRes;
    AppState.filteredComplaints = [...cmpRes];

    // 첫 번째 민원 자동 선택
    if (AppState.filteredComplaints.length > 0) {
      AppState.selectedComplaint = AppState.filteredComplaints[0];
      bindComplaintDetail(AppState.selectedComplaint);
    }

    statusLabel.textContent = "온라인 데모 (Mock Engine)";
  } catch (err) {
    console.error("[ERROR] 데이터 로딩 실패:", err);
    statusLabel.textContent = "데이터 로딩 오류";
  }
}

// -------------------------------------------------------------
// 대시보드 (KPI 카드 & Chart.js 차트 렌더링)
// -------------------------------------------------------------
function renderDashboard() {
  const kpi = AppState.summaryKpi;
  if (!kpi) return;

  document.getElementById('kpiTotalFac').textContent = kpi.totalFacilities.toLocaleString();
  document.getElementById('kpiNormalFac').textContent = kpi.normalFacilities.toLocaleString();
  document.getElementById('kpiTotalCmp').textContent = kpi.totalComplaints.toLocaleString();
  document.getElementById('kpiResolvedCmp').textContent = kpi.resolvedComplaints.toLocaleString();

  // 1. 자치구별 민원 및 시설물 분포 차트 (Bar Chart)
  const ctxDistrict = document.getElementById('chartDistrict').getContext('2d');
  const distCounts = {};
  AppState.ds_facilities.forEach(f => {
    distCounts[f.DISTRICT] = (distCounts[f.DISTRICT] || 0) + 1;
  });

  new Chart(ctxDistrict, {
    type: 'bar',
    data: {
      labels: Object.keys(distCounts),
      datasets: [{
        label: '공공시설물 설치 대수',
        data: Object.values(distCounts),
        backgroundColor: 'rgba(0, 210, 255, 0.6)',
        borderColor: '#00d2ff',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });

  // 2. 민원 처리 상태 파이 차트
  const ctxStatus = document.getElementById('chartStatus').getContext('2d');
  const statusCounts = { 'RECEIVED': 0, 'ASSIGNED': 0, 'IN_PROGRESS': 0, 'RESOLVED': 0, 'REJECTED': 0 };
  AppState.ds_complaints.forEach(c => {
    if (statusCounts[c.STATUS] !== undefined) statusCounts[c.STATUS]++;
  });

  new Chart(ctxStatus, {
    type: 'doughnut',
    data: {
      labels: ['접수대기', '부서배정', '처리중', '해결완료', '반려'],
      datasets: [{
        data: Object.values(statusCounts),
        backgroundColor: [
          '#60a5fa', '#a78bfa', '#fbbf24', '#34d399', '#f87171'
        ],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 12 } }
      }
    }
  });

  // 3. 최근 긴급 민원 피드
  const alertList = document.getElementById('recentAlertList');
  alertList.innerHTML = '';
  const urgentComplaints = AppState.ds_complaints.slice(0, 5);
  urgentComplaints.forEach(c => {
    const li = document.createElement('div');
    li.className = 'alert-item';
    li.style.cssText = 'padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;';
    li.innerHTML = `
      <div>
        <span class="badge ${getStatusBadgeClass(c.STATUS)}" style="margin-right: 8px;">${getStatusName(c.STATUS)}</span>
        <strong style="color: #f8fafc; font-size: 13px;">${escapeHtml(c.TITLE)}</strong>
        <p style="font-size: 11px; color: #64748b; margin-top: 4px;">${c.OCCUR_ADDRESS} | ${c.REG_DATE}</p>
      </div>
      <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="viewComplaintDetail('${c.COMPLAINT_ID}')">상세</button>
    `;
    alertList.appendChild(li);
  });
}

// -------------------------------------------------------------
// 넥사크로 시민 통합 민원 관리 (Grid & Detail Form 바인딩)
// -------------------------------------------------------------
function renderComplaintsTable() {
  const tbody = document.getElementById('complaintGridBody');
  tbody.innerHTML = '';

  const total = AppState.filteredComplaints.length;
  const startIdx = (AppState.complaintPage - 1) * AppState.pageSize;
  const pageItems = AppState.filteredComplaints.slice(startIdx, startIdx + AppState.pageSize);

  document.getElementById('complaintCountTotal').textContent = total.toLocaleString();
  document.getElementById('pageInfoText').textContent = 
    `${AppState.complaintPage} / ${Math.max(1, Math.ceil(total / AppState.pageSize))} 페이지 (총 ${total.toLocaleString()}건)`;

  pageItems.forEach((c, idx) => {
    const tr = document.createElement('tr');
    if (AppState.selectedComplaint && AppState.selectedComplaint.COMPLAINT_ID === c.COMPLAINT_ID) {
      tr.classList.add('selected');
    }
    tr.innerHTML = `
      <td style="text-align: center;">${startIdx + idx + 1}</td>
      <td style="text-align: center; font-family: monospace;">${c.COMPLAINT_ID}</td>
      <td style="text-align: center;"><span style="color:#00d2ff;">[${c.CATEGORY}]</span></td>
      <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(c.TITLE)}</td>
      <td style="text-align: center;">${c.DISTRICT}</td>
      <td style="text-align: center;">${maskName(c.PETITIONER_NAME)}</td>
      <td style="text-align: center; color: #94a3b8; font-size: 12px;">${c.REG_DATE}</td>
      <td style="text-align: center;"><span class="badge ${getStatusBadgeClass(c.STATUS)}">${getStatusName(c.STATUS)}</span></td>
    `;
    tr.addEventListener('click', () => {
      document.querySelectorAll('#complaintGridBody tr').forEach(r => r.classList.remove('selected'));
      tr.classList.add('selected');
      AppState.selectedComplaint = c;
      bindComplaintDetail(c);
    });
    tbody.appendChild(tr);
  });
}

function bindComplaintDetail(c) {
  if (!c) return;
  document.getElementById('dtl_id').value = c.COMPLAINT_ID;
  document.getElementById('dtl_title').value = c.TITLE;
  document.getElementById('dtl_addr').value = c.OCCUR_ADDRESS;
  document.getElementById('dtl_category').value = c.CATEGORY;
  document.getElementById('dtl_petitioner').value = `${maskName(c.PETITIONER_NAME)} (${c.PETITIONER_TEL || '연락처 없음'})`;
  document.getElementById('dtl_content').value = c.CONTENT;
  document.getElementById('dtl_status').value = c.STATUS;
  document.getElementById('dtl_handler').value = c.HANDLER_NAME || '';
  document.getElementById('dtl_resolve').value = c.RESOLVE_COMMENT || '';
}

// -------------------------------------------------------------
// 시설물 관리 & 점검 이력 (Master-Detail)
// -------------------------------------------------------------
function renderFacilitiesTable() {
  const tbody = document.getElementById('facilityGridBody');
  tbody.innerHTML = '';

  AppState.ds_facilities.forEach((f, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="text-align: center; font-family: monospace;">${f.FAC_ID}</td>
      <td><strong>${escapeHtml(f.FAC_NAME)}</strong></td>
      <td style="text-align: center;"><span style="color: #38bdf8;">${f.FAC_TYPE}</span></td>
      <td style="text-align: center;">${f.DISTRICT}</td>
      <td>${f.LOCATION_ADDR}</td>
      <td style="text-align: center;"><span class="badge ${getFacStatusBadge(f.OP_STATUS)}">${getFacStatusName(f.OP_STATUS)}</span></td>
      <td style="text-align: center; color: #94a3b8;">${f.INSTALL_DATE}</td>
      <td style="text-align: center;">${f.MANAGE_DEPT}</td>
    `;
    tr.addEventListener('click', () => {
      document.querySelectorAll('#facilityGridBody tr').forEach(r => r.classList.remove('selected'));
      tr.classList.add('selected');
      AppState.selectedFacility = f;
      renderInspectionsForFacility(f.FAC_ID);
    });
    tbody.appendChild(tr);
  });

  // 첫 번째 시설물 자동 점검 이력 표시
  if (AppState.ds_facilities.length > 0) {
    renderInspectionsForFacility(AppState.ds_facilities[0].FAC_ID);
  }
}

function renderInspectionsForFacility(facId) {
  const tbody = document.getElementById('inspGridBody');
  tbody.innerHTML = '';
  
  const relatedInsps = AppState.ds_inspections.filter(i => i.FAC_ID === facId);
  document.getElementById('selectedFacLabel').textContent = `[${facId}] 유지보수 점검 이력 (${relatedInsps.length}건)`;

  if (relatedInsps.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #64748b; padding: 20px;">등록된 점검 이력이 없습니다.</td></tr>`;
    return;
  }

  relatedInsps.forEach(i => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="text-align: center; font-family: monospace;">${i.INSP_ID}</td>
      <td style="text-align: center;">${i.INSP_DATE}</td>
      <td style="text-align: center;">${i.INSP_TYPE}</td>
      <td style="text-align: center;"><span class="badge ${i.INSP_STATUS === 'PASS' ? 'badge-resolved' : 'badge-error'}">${i.INSP_STATUS}</span></td>
      <td style="text-align: center;">${i.INSPECTOR_NAME}</td>
      <td>${escapeHtml(i.ACTION_DETAILS)}</td>
      <td style="text-align: right; color: #fbbf24;">${(i.REPAIR_COST || 0).toLocaleString()} 원</td>
      <td style="text-align: center; color: #94a3b8;">${i.NEXT_INSP_DATE}</td>
    `;
    tbody.appendChild(tr);
  });
}

// -------------------------------------------------------------
// IoT 실시간 센서 텔레메트리
// -------------------------------------------------------------
function renderSensorMonitoring() {
  const grid = document.getElementById('sensorLogsBody');
  if (!grid) return;
  grid.innerHTML = '';

  const sampleLogs = AppState.ds_sensor_logs.slice(0, 20);
  sampleLogs.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="text-align: center;">${s.LOG_ID}</td>
      <td style="text-align: center; font-family: monospace;">${s.FAC_ID}</td>
      <td style="text-align: center;"><span style="color: #a78bfa;">${s.SENSOR_TYPE}</span></td>
      <td style="text-align: right; font-weight: bold; color: #00d2ff;">${s.METRIC_VAL} ${s.UNIT}</td>
      <td style="text-align: center;"><span class="badge ${s.STATUS_FLAG === 'OK' ? 'badge-resolved' : (s.STATUS_FLAG === 'WARN' ? 'badge-in-progress' : 'badge-error')}">${s.STATUS_FLAG}</span></td>
      <td style="text-align: center; color: #94a3b8;">${s.LOGGED_AT}</td>
    `;
    grid.appendChild(tr);
  });
}

// -------------------------------------------------------------
// 이벤트 핸들러 및 유틸리티
// -------------------------------------------------------------
function initEventListeners() {
  // 민원 검색 버튼
  document.getElementById('btnSearchComplaint').addEventListener('click', () => {
    const dist = document.getElementById('searchDistrict').value;
    const status = document.getElementById('searchStatus').value;
    const keyword = document.getElementById('searchKeyword').value.trim().toLowerCase();

    AppState.filteredComplaints = AppState.ds_complaints.filter(c => {
      if (dist !== 'ALL' && c.DISTRICT !== dist) return false;
      if (status !== 'ALL' && c.STATUS !== status) return false;
      if (keyword && !c.TITLE.toLowerCase().includes(keyword) && !c.CONTENT.toLowerCase().includes(keyword)) return false;
      return true;
    });

    AppState.complaintPage = 1;
    renderComplaintsTable();
    if (AppState.filteredComplaints.length > 0) {
      AppState.selectedComplaint = AppState.filteredComplaints[0];
      bindComplaintDetail(AppState.selectedComplaint);
    }
  });

  // 검색 초기화
  document.getElementById('btnResetSearch').addEventListener('click', () => {
    document.getElementById('searchDistrict').value = 'ALL';
    document.getElementById('searchStatus').value = 'ALL';
    document.getElementById('searchKeyword').value = '';
    AppState.filteredComplaints = [...AppState.ds_complaints];
    AppState.complaintPage = 1;
    renderComplaintsTable();
  });

  // 페이징 버튼들
  document.getElementById('btnPrevPage').addEventListener('click', () => {
    if (AppState.complaintPage > 1) {
      AppState.complaintPage--;
      renderComplaintsTable();
    }
  });

  document.getElementById('btnNextPage').addEventListener('click', () => {
    const maxPage = Math.ceil(AppState.filteredComplaints.length / AppState.pageSize);
    if (AppState.complaintPage < maxPage) {
      AppState.complaintPage++;
      renderComplaintsTable();
    }
  });

  // 조치 저장 버튼
  document.getElementById('btnSaveComplaint').addEventListener('click', () => {
    if (!AppState.selectedComplaint) {
      alert("선택된 민원이 없습니다.");
      return;
    }
    const newStatus = document.getElementById('dtl_status').value;
    const newHandler = document.getElementById('dtl_handler').value;
    const newComment = document.getElementById('dtl_resolve').value;

    AppState.selectedComplaint.STATUS = newStatus;
    AppState.selectedComplaint.HANDLER_NAME = newHandler;
    AppState.selectedComplaint.RESOLVE_COMMENT = newComment;

    alert(`[조치 완료] 민원 (${AppState.selectedComplaint.COMPLAINT_ID}) 처리가 정상 저장되었습니다.`);
    renderComplaintsTable();
  });

  // 엑셀 CSV 다운로드
  document.getElementById('btnExportExcel').addEventListener('click', () => {
    exportComplaintsToCSV();
  });
}

function exportComplaintsToCSV() {
  let csv = "\uFEFF접수번호,유형,민원제목,발생구역,민원인,접수일시,상태,담당자\n";
  AppState.filteredComplaints.forEach(c => {
    csv += `"${c.COMPLAINT_ID}","${c.CATEGORY}","${c.TITLE.replace(/"/g, '""')}","${c.DISTRICT}","${c.PETITIONER_NAME}","${c.REG_DATE}","${c.STATUS}","${c.HANDLER_NAME || ''}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `스마트시티_민원데이터_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function viewComplaintDetail(id) {
  const found = AppState.ds_complaints.find(c => c.COMPLAINT_ID === id);
  if (found) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector('[data-target="tab-complaints"]').classList.add('active');
    document.getElementById('tab-complaints').classList.add('active');
    AppState.selectedComplaint = found;
    bindComplaintDetail(found);
    renderComplaintsTable();
  }
}

// 헬퍼 함수들
function getStatusBadgeClass(status) {
  switch (status) {
    case 'RECEIVED': return 'badge-received';
    case 'ASSIGNED': return 'badge-assigned';
    case 'IN_PROGRESS': return 'badge-in-progress';
    case 'RESOLVED': return 'badge-resolved';
    default: return 'badge-error';
  }
}

function getStatusName(status) {
  const map = {
    'RECEIVED': '접수',
    'ASSIGNED': '배정',
    'IN_PROGRESS': '처리중',
    'RESOLVED': '완료',
    'REJECTED': '반려'
  };
  return map[status] || status;
}

function getFacStatusBadge(status) {
  switch (status) {
    case 'NORMAL': return 'badge-resolved';
    case 'WARNING': return 'badge-in-progress';
    case 'ERROR': return 'badge-error';
    default: return 'badge-assigned';
  }
}

function getFacStatusName(status) {
  const map = { 'NORMAL': '정상가동', 'WARNING': '점검필요', 'ERROR': '장애/고장', 'SHUTDOWN': '가동중지' };
  return map[status] || status;
}

function maskName(name) {
  if (!name || name.length < 2) return name;
  if (name.length === 2) return name[0] + '*';
  return name[0] + '*'.repeat(name.length - 2) + name[name.length - 1];
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
