package com.smartad.server.controller;

import com.smartad.server.common.Result;
import com.smartad.server.dto.request.LogReportRequest;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@Slf4j
@Tag(name = "数据日志接口")
@RestController
@RequestMapping("/api/data")
public class DataLogController {

    @Operation(summary = "用户行为日志上报（第一阶段写日志）")
    @PostMapping("/log/report")
    public Result<Void> reportLog(@Valid @RequestBody LogReportRequest request) {
        // 第一阶段：写日志到控制台，第三阶段接入ClickHouse
        log.info("[用户行为日志] userId={}, eventType={}, adId={}, device={}, city={}, time={}",
                request.getUserId(), request.getEventType(), request.getAdId(),
                request.getDevice(), request.getCity(), request.getEventTime());
        return Result.success("日志上报成功", null);
    }
}
