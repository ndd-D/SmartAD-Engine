package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AiAlertPushRequest {

    @NotBlank(message = "告警内容不能为空")
    private String alertContent;

    /** 接口异常/策略执行失败 */
    @NotBlank(message = "告警类型不能为空")
    private String alertType;

    private String relatedId;
}
