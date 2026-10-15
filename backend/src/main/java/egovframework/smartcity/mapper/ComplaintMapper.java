package egovframework.smartcity.mapper;

import egovframework.smartcity.model.ComplaintVO;
import egovframework.smartcity.model.PageVO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ComplaintMapper {
    List<ComplaintVO> selectComplaintList(PageVO pageVO);
    int selectComplaintCount(PageVO pageVO);
    ComplaintVO selectComplaintDetail(String complaintId);
    int updateComplaintStatus(ComplaintVO complaintVO);
}
