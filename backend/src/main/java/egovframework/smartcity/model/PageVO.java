package egovframework.smartcity.model;

import lombok.Data;

/**
 * 대용량 데이터 페이징 검색용 VO
 */
@Data
public class PageVO {
    private int page = 1;
    private int pageSize = 20;
    private String district;
    private String status;
    private String facType;
    private String keyword;

    public int getOffset() {
        return (this.page - 1) * this.pageSize;
    }
}
