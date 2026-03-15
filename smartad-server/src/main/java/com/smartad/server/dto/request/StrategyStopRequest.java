package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class StrategyStopRequest {

    @NotBlank(message = "strategyId不能为空")
    private String strategyId;

    /** 暂停/下线 */
    @NotBlank(message = "operateType不能为空")
    private String operateType;
}
