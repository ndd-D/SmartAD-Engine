package com.smartad.server.controller;

import com.smartad.server.common.Result;
import com.smartad.server.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Tag(name = "报表接口（前端）")
@RestController
@RequestMapping("/api/report")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @Operation(summary = "投放数据报表列表（分页）")
    @GetMapping("/list")
    public Result<Object> getReportList(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String strategyId,
            @RequestParam(required = false) String channel,
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate) {
        return Result.success("查询成功",
                reportService.getReportList(page, pageSize, strategyId, channel, startDate, endDate));
    }

    @Operation(summary = "投放数据报表详情（按策略汇总）")
    @GetMapping("/detail/{strategyId}")
    public Result<Map<String, Object>> getReportDetail(
            @PathVariable String strategyId,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        return Result.success("查询成功", reportService.getAdReport(strategyId, startTime, endTime));
    }

    @Operation(summary = "投放数据报表查询（旧接口兼容）")
    @GetMapping("/adData")
    public Result<Map<String, Object>> getAdReport(
            @RequestParam String strategyId,
            @RequestParam(required = false) String startTime,
            @RequestParam(required = false) String endTime) {
        return Result.success("查询成功", reportService.getAdReport(strategyId, startTime, endTime));
    }
}

