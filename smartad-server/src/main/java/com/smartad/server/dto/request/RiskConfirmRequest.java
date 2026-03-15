package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class RiskConfirmRequest {

    @NotBlank(message = "strategyId不能为空")
    private String strategyId;

    @NotNull(message = "userId不能为空")
    private Long userId;

    /** 同意/拒绝 */
    @NotBlank(message = "confirmResult不能为空")
    private String confirmResult;
}
