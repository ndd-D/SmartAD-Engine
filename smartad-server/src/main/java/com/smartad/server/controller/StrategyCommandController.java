package com.smartad.server.controller;

import com.smartad.server.common.Result;
import com.smartad.server.dto.request.CommandReplyRequest;
import com.smartad.server.dto.request.CommandRequest;
import com.smartad.server.service.CommandService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Tag(name = "策略指令接口（前端）")
@RestController
@RequestMapping("/api/strategy")
@RequiredArgsConstructor
public class StrategyCommandController {

    private final CommandService commandService;
    private final com.smartad.server.service.StrategyService strategyService;

    @Operation(summary = "自然语言投放指令下发")
    @PostMapping("/command")
    public Result<Map<String, String>> submitCommand(@Valid @RequestBody CommandRequest request) {
        return Result.success("指令已提交", commandService.submitCommand(request));
    }

    @Operation(summary = "查询指令执行状态")
    @GetMapping("/command/status")
    public Result<Map<String, Object>> getCommandStatus(@RequestParam String commandId) {
        return Result.success("查询成功", commandService.getCommandStatus(commandId));
    }

    @Operation(summary = "AI提问前端回复")
    @PostMapping("/command/reply")
    public Result<Map<String, String>> replyCommand(@Valid @RequestBody CommandReplyRequest request) {
        return Result.success("回复已提交，AI将继续处理", commandService.replyCommand(request));
    }

    @Operation(summary = "查询策略详情")
    @GetMapping("/info")
    public Result<Object> getStrategyInfo(@RequestParam String strategyId) {
        return Result.success("查询成功", strategyService.getStrategyInfo(strategyId));
    }

    @Operation(summary = "策略确认上线/编辑")
    @PostMapping("/confirm")
    public Result<Map<String, Object>> confirmStrategy(
            @Valid @RequestBody com.smartad.server.dto.request.StrategyConfirmRequest request) {
        return Result.success("操作成功", strategyService.confirmStrategy(request));
    }

    @Operation(summary = "高风险策略人工确认")
    @PostMapping("/risk/confirm")
    public Result<Map<String, Object>> riskConfirm(
            @Valid @RequestBody com.smartad.server.dto.request.RiskConfirmRequest request) {
        return Result.success("高风险策略已确认", strategyService.riskConfirm(request));
    }

    @Operation(summary = "策略暂停/下线")
    @PostMapping("/stop")
    public Result<Map<String, String>> stopStrategy(
            @Valid @RequestBody com.smartad.server.dto.request.StrategyStopRequest request) {
        return Result.success("操作成功", strategyService.stopStrategy(request));
    }

    @Operation(summary = "策略列表分页查询")
    @GetMapping("/list")
    public Result<Object> listStrategies(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String channel) {
        return Result.success("查询成功", strategyService.listStrategies(page, pageSize, status, channel));
    }
}
