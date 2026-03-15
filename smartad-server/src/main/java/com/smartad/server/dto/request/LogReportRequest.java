package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class LogReportRequest {

    @NotBlank
    private String userId;

    /** click/convert */
    @NotBlank
    private String eventType;

    @NotBlank
    private String adId;

    private String eventTime;

    private String device;

    private String city;
}
