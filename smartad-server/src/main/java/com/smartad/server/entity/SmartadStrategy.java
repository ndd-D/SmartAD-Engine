package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 投放策略表
 */
@Data
@TableName("smartad_strategy")
public class SmartadStrategy {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String strategyId;

    private String commandId;

    private Long crowdId;

    private String crowdTag;

    /** 投放渠道（单个），如：抖音 */
    private String channel;

    private BigDecimal budgetDay;

    private Integer bidPrice;

    /**
     * 状态：pending/approved/rejected/running/paused/offline
     */
    private String status;

    private String aiReason;

    private Integer aiScore;

    private String adjustType;

    private String adjustReason;

    private String channelAdId;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
