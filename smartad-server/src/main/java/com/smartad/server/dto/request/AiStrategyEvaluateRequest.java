package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class AiStrategyEvaluateRequest {

    @NotBlank(message = "strategyId不能为空")
    private String strategyId;

    @NotBlank(message = "commandId不能为空")
    private String commandId;

    /** 成功/失败 */
    @NotBlank(message = "evaluateResult不能为空")
    private String evaluateResult;

    private BigDecimal roi;

    private BigDecimal budgetDeviation;

    private String evaluateReason;
}
