package com.smartad.server.controller;

import com.smartad.server.common.Result;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadCommand;
import com.smartad.server.entity.SmartadCrowd;
import com.smartad.server.entity.SmartadStrategy;
import com.smartad.server.service.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(name = "AI接口（Python AI专用）")
@RestController
@RequestMapping("/api/ai")
@RequiredArgsConstructor
public class AiController {

    private final CommandService commandService;
    private final StrategyService strategyService;
    private final CrowdService crowdService;
    private final ReportService reportService;
    private final AlertService alertService;

    // ─────────────────── 指令相关 ───────────────────

    @Operation(summary = "AI获取待处理指令列表")
    @GetMapping("/command/list")
    public Result<List<SmartadCommand>> getPendingCommands(
            @RequestParam(defaultValue = "待AI处理") String status) {
        return Result.success("查询成功", commandService.getPendingCommandsForAi(status));
    }

    @Operation(summary = "AI更新指令处理状态")
    @PostMapping("/command/update")
    public Result<Void> updateCommand(@Valid @RequestBody AiCommandUpdateRequest request) {
        commandService.updateCommandByAi(request);
        return Result.success("状态更新成功", null);
    }

    // ─────────────────── 人群画像 ───────────────────

    @Operation(summary = "AI查询用户画像数据（按标签）")
    @GetMapping("/crowd/info")
    public Result<SmartadCrowd> getCrowdInfo(@RequestParam String crowdTag) {
        return Result.success("查询成功", crowdService.getCrowdInfo(crowdTag));
    }

    @Operation(summary = "AI获取所有用户画像列表")
    @GetMapping("/crowd/list")
    public Result<List<SmartadCrowd>> getCrowdList() {
        return Result.success("查询成功", crowdService.listAllCrowds());
    }

    // ─────────────────── 报表相关 ───────────────────

    @Operation(summary = "AI查询历史投放效果数据（按人群+渠道）")
    @GetMapping("/report/history")
    public Result<Map<String, Object>> getHistoryReport(
            @RequestParam(required = false) String crowdTag,
            @RequestParam(required = false) String channel) {
        return Result.success("查询成功", reportService.getHistoryReport(crowdTag, channel));
    }

    @Operation(summary = "AI获取实时投放数据（用于策略优化）")
    @GetMapping("/report/realTime")
    public Result<Map<String, Object>> getRealTimeData(@RequestParam String strategyId) {
        return Result.success("查询成功", reportService.getRealTimeData(strategyId));
    }

    @Operation(summary = "AI按策略获取近N天报表（用于评估）")
    @GetMapping("/report/strategy")
    public Result<List<Map<String, Object>>> getStrategyReport(
            @RequestParam String strategyId,
            @RequestParam(defaultValue = "7") Integer days) {
        return Result.success("查询成功", reportService.getStrategyReport(strategyId, days));
    }

    // ─────────────────── 策略相关 ───────────────────

    @Operation(summary = "AI生成并同步策略到Java后端")
    @PostMapping("/strategy/sync")
    public Result<Map<String, String>> syncStrategy(@Valid @RequestBody AiStrategySyncRequest request) {
        return Result.success("策略同步成功", strategyService.syncStrategyFromAi(request));
    }

    @Operation(summary = "AI获取所有投放中策略列表")
    @GetMapping("/strategy/active")
    public Result<List<SmartadStrategy>> getActiveStrategies() {
        return Result.success("查询成功", strategyService.getActiveStrategies());
    }

    @Operation(summary = "AI自动调整投放策略")
    @PostMapping("/strategy/adjust")
    public Result<Void> adjustStrategy(@Valid @RequestBody AiStrategyAdjustRequest request) {
        strategyService.adjustStrategy(request);
        return Result.success("策略调整成功", null);
    }

    @Operation(summary = "AI上报策略评估结果")
    @PostMapping("/strategy/evaluate")
    public Result<Map<String, String>> evaluateStrategy(@Valid @RequestBody AiStrategyEvaluateRequest request) {
        Map<String, String> result = strategyService.evaluateStrategy(request);
        return Result.success("评估结果上报成功", result);
    }

    // ─────────────────── 告警 ───────────────────

    @Operation(summary = "AI推送系统告警")
    @PostMapping("/notice/alert/push")
    public Result<Map<String, String>> pushAlert(@Valid @RequestBody AiAlertPushRequest request) {
        alertService.pushAlert(request);
        // alertId 由 AlertServiceImpl 内部生成，从返回的alert读取
        return Result.success("告警推送成功", Map.of("alertId", "pushed"));
    }
}

