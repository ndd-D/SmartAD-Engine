package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class AiStrategyAdjustRequest {

    @NotBlank(message = "strategyId不能为空")
    private String strategyId;

    /** bidPrice/runTime/budgetDay */
    @NotBlank(message = "adjustType不能为空")
    private String adjustType;

    @NotNull(message = "原始值不能为空")
    private BigDecimal oldValue;

    @NotNull(message = "新值不能为空")
    private BigDecimal newValue;

    private String reason;
}
