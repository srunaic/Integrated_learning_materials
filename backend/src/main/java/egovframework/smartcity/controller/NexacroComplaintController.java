package egovframework.smartcity.controller;

import egovframework.smartcity.mapper.ComplaintMapper;
import egovframework.smartcity.model.ComplaintVO;
import egovframework.smartcity.model.PageVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 넥사크로(Nexacro) 및 웹 프론트엔드 연동용 민원 관리 컨트롤러
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*") // 로컬 개발 및 교차 출처 리소스 공유 허용
public class NexacroComplaintController {

    @Autowired
    private ComplaintMapper complaintMapper;

    /**
     * 민원 목록 페이징 조회 API
     * (Nexacro ds_search -> ds_complaints 바인딩 호환)
     */
    @GetMapping({"/complaints", "/nexacro/complaints"})
    public ResponseEntity<Map<String, Object>> getComplaints(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int pageSize,
            @RequestParam(required = false) String district,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword
    ) {
        PageVO pageVO = new PageVO();
        pageVO.setPage(page);
        pageVO.setPageSize(pageSize);
        pageVO.setDistrict(district);
        pageVO.setStatus(status);
        pageVO.setKeyword(keyword);

        List<ComplaintVO> list = complaintMapper.selectComplaintList(pageVO);
        int totalCount = complaintMapper.selectComplaintCount(pageVO);

        Map<String, Object> result = new HashMap<>();
        result.put("errorCode", 0);
        result.put("errorMsg", "SUCCESS");
        result.put("totalCount", totalCount);
        result.put("page", page);
        result.put("pageSize", pageSize);
        result.put("totalPages", (int) Math.ceil((double) totalCount / pageSize));
        result.put("ds_complaints", list);

        return ResponseEntity.ok(result);
    }

    /**
     * 민원 상세 조회
     */
    @GetMapping({"/complaint/{id}", "/nexacro/complaint/{id}"})
    public ResponseEntity<Map<String, Object>> getComplaintDetail(@PathVariable String id) {
        ComplaintVO vo = complaintMapper.selectComplaintDetail(id);
        Map<String, Object> result = new HashMap<>();
        result.put("errorCode", vo != null ? 0 : -1);
        result.put("data", vo);
        return ResponseEntity.ok(result);
    }

    /**
     * 민원 조치 및 상태 저장 (Nexacro Form 저장 트랜잭션)
     */
    @PostMapping({"/complaint/save", "/nexacro/complaint/save"})
    public ResponseEntity<Map<String, Object>> saveComplaint(@RequestBody ComplaintVO vo) {
        int updated = complaintMapper.updateComplaintStatus(vo);
        Map<String, Object> result = new HashMap<>();
        result.put("errorCode", updated > 0 ? 0 : -1);
        result.put("errorMsg", updated > 0 ? "정상 처리되었습니다." : "업데이트 대상이 없습니다.");
        return ResponseEntity.ok(result);
    }
}
