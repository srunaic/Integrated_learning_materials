package egovframework.smartcity.model;

import lombok.Data;

/**
 * 스마트시티 공공 시설물 VO
 */
@Data
public class FacilityVO {
    private String facId;
    private String facName;
    private String facType;
    private String district;
    private String locationAddr;
    private Double latitude;
    private Double longitude;
    private String installDate;
    private String opStatus;
    private String manageDept;
    private String managerName;
    private String managerPhone;
    private String lastInspDate;
    private String remarks;
}
