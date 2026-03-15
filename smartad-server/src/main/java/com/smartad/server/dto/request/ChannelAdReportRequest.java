package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class ChannelAdReportRequest {

    @NotBlank
    private String adId;

    @NotBlank
    private String channel;

    private Long expose;
    private Long click;
    private Long convert;
    private BigDecimal cost;
    private BigDecimal roi;
}
