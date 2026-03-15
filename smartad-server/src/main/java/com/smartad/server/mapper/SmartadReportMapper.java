package com.smartad.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartad.server.entity.SmartadReport;
import lombok.Data;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.math.BigDecimal;

@Mapper
public interface SmartadReportMapper extends BaseMapper<SmartadReport> {

    /**
     * 查询某人群+渠道的历史平均投放数据（供AI调用）
     */
    @Select("SELECT AVG(r.ctr) as avgClickRate, " +
            "AVG(CASE WHEN r.clicks > 0 THEN r.conversions / r.clicks ELSE 0 END) as avgConvertRate, " +
            "AVG(r.roi) as avgRoi FROM smartad_report r " +
            "WHERE r.crowd_tag = #{crowdTag} AND r.channel = #{channel} " +
            "AND r.report_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)")
    HistoryAvg queryHistoryAvg(String crowdTag, String channel);

    @Data
    class HistoryAvg {
        private BigDecimal avgClickRate;
        private BigDecimal avgConvertRate;
        private BigDecimal avgRoi;
    }
}

