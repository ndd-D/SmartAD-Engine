package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 报表表
 */
@Data
@TableName("smartad_report")
public class SmartadReport {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String strategyId;

    private String crowdTag;

    private String channel;

    private LocalDate reportDate;

    private Long impressions;

    private Long clicks;

    private BigDecimal ctr;

    private BigDecimal cost;

    private Integer conversions;

    private BigDecimal roi;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
