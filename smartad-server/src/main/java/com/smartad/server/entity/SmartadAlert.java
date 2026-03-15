package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 告警表
 */
@Data
@TableName("smartad_alert")
public class SmartadAlert {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String alertId;

    private String strategyId;

    private String alertType;

    private String alertLevel;

    private String alertMessage;

    /** 状态：unread/read */
    private String status;

    @TableField("confirmed_at")
    private LocalDateTime confirmedAt;

    @TableField("created_at")
    private LocalDateTime createdAt;

    @TableField("updated_at")
    private LocalDateTime updatedAt;
}
