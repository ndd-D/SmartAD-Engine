package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("smartad_log")
public class SmartadLog {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 事件类型：click / impression / conversion */
    private String eventType;

    /** 策略ID */
    private String strategyId;

    /** 渠道标识 */
    private String channel;

    /** 广告位 */
    private String adSlot;

    /** 用户设备标识 */
    private String deviceId;

    /** 用户ID（可为空） */
    private Long userId;

    /** 扩展JSON */
    private String extra;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;
}
