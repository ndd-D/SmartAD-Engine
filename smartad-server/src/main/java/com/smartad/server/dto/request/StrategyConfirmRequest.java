package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class StrategyConfirmRequest {

    @NotBlank(message = "strategyId不能为空")
    private String strategyId;

    /** 上线/编辑 */
    @NotBlank(message = "operateType不能为空")
    private String operateType;

    private EditData editData;

    @Data
    public static class EditData {
        private Integer budgetDay;
        private BigDecimal bidPrice;
    }
}
