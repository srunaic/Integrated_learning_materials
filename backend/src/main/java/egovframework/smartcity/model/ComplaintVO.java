package egovframework.smartcity.model;

import lombok.Data;
import java.util.Date;

/**
 * 스마트시티 시민 통합 민원 VO
 */
@Data
public class ComplaintVO {
    private String complaintId;
    private String title;
    private String category;
    private String content;
    private String petitionerName;
    private String petitionerTel;
    private String occurAddress;
    private String district;
    private String relatedFacId;
    private String regDate;
    private String status;
    private String assignedDept;
    private String handlerName;
    private String resolveDate;
    private String resolveComment;
    private Integer satisfaction;
}
