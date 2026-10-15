package egovframework.smartcity.controller;

import egovframework.smartcity.mapper.FacilityMapper;
import egovframework.smartcity.model.FacilityVO;
import egovframework.smartcity.model.PageVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 공공시설물 관리 컨트롤러
 */
@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class FacilityController {

    @Autowired
    private FacilityMapper facilityMapper;

    @GetMapping({"/facilities", "/nexacro/facilities"})
    public ResponseEntity<Map<String, Object>> getFacilities(
            @RequestParam(required = false) String district,
            @RequestParam(required = false) String facType,
            @RequestParam(required = false) String status
    ) {
        PageVO pageVO = new PageVO();
        pageVO.setDistrict(district);
        pageVO.setFacType(facType);
        pageVO.setStatus(status);

        List<FacilityVO> list = facilityMapper.selectFacilityList(pageVO);
        int totalCount = facilityMapper.selectFacilityCount(pageVO);

        Map<String, Object> result = new HashMap<>();
        result.put("errorCode", 0);
        result.put("errorMsg", "SUCCESS");
        result.put("totalCount", totalCount);
        result.put("ds_facilities", list);

        return ResponseEntity.ok(result);
    }
}
