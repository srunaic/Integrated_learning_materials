package egovframework.smartcity.mapper;

import egovframework.smartcity.model.FacilityVO;
import egovframework.smartcity.model.PageVO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface FacilityMapper {
    List<FacilityVO> selectFacilityList(PageVO pageVO);
    int selectFacilityCount(PageVO pageVO);
}
