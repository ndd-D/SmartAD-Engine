package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AiCommandUpdateRequest {

    @NotBlank(message = "commandId不能为空")
    private String commandId;

    /** 处理中/已完成/处理失败/AI提问中 */
    @NotBlank(message = "status不能为空")
    private String status;

    private String failReason;

    private String aiQuestion;
}
