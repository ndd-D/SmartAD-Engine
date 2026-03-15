package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 投放指令表
 */
@Data
@TableName("smartad_command")
public class SmartadCommand {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 对应数据库 command_id */
    private String commandId;

    /** 对应数据库 operator_id */
    @TableField("operator_id")
    private Long userId;

    /** 对应数据库 command_text */
    private String commandText;

    /**
     * 状态：待AI处理/处理中/AI提问中/已生成策略/执行失败
     */
    private String status;

    /** 对应数据库 ai_question */
    private String aiQuestion;

    /** 对应数据库 fail_reason */
    private String failReason;

    /** 对应数据库 strategy_id */
    private String strategyId;

    /** 对应数据库 user_reply */
    @TableField("user_reply")
    private String replyContent;

    /** 对应数据库 reply_time */
    private LocalDateTime replyTime;

    /** 对应数据库 created_at */
    @TableField(value = "created_at", fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /** 对应数据库 updated_at */
    @TableField(value = "updated_at", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
