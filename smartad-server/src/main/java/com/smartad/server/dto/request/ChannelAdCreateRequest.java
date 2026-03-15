package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class ChannelAdCreateRequest {

    @NotBlank
    private String strategyId;

    @NotBlank
    private String channel;

    @NotBlank
    private String adName;

    @NotNull
    private Integer budgetDay;

    @NotNull
    private BigDecimal bidPrice;

    private String crowd;

    private String runTime;
}
