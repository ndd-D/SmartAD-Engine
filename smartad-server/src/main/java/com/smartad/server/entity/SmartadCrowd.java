package com.smartad.server.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 人群画像表
 */
@Data
@TableName("smartad_crowd")
public class SmartadCrowd {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String crowdTag;

    private Long userCount;

    /** JSON数组: ["美妆","护肤"] */
    private String preferTags;

    private String activeTime;

    private String ageRange;

    private String gender;

    private String cityLevel;

    @TableField(value = "updated_at", fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
}
