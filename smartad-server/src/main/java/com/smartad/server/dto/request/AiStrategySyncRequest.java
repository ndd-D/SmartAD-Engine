package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class AiStrategySyncRequest {

    @NotBlank(message = "commandId不能为空")
    private String commandId;

    @NotBlank(message = "策略名称不能为空")
    private String strategyName;

    @NotNull(message = "渠道不能为空")
    private List<String> channels;

    @NotNull(message = "日预算不能为空")
    private Integer budgetDay;

    @NotBlank(message = "人群标签不能为空")
    private String crowdTag;

    @NotNull(message = "出价不能为空")
    private BigDecimal bidPrice;

    @NotBlank(message = "投放时段不能为空")
    private String runTime;

    private String productType;

    /** 普通/高风险 */
    private String riskLevel = "普通";
}
