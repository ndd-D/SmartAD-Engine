package com.smartad.server.controller;

import com.smartad.server.common.Result;
import com.smartad.server.service.AlertService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@Tag(name = "告警接口（前端）")
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class AlertController {

    private final AlertService alertService;

    @Operation(summary = "查询系统告警列表")
    @GetMapping("/alert/list")
    public Result<Object> listAlerts(
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String alertLevel,
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer pageSize) {
        return Result.success("查询成功", alertService.listAlerts(page, pageSize, status, alertLevel));
    }

    @Operation(summary = "确认告警（标记为已读）")
    @PostMapping("/alert/confirm/{alertId}")
    public Result<Void> confirmAlert(@PathVariable String alertId) {
        alertService.confirmAlert(alertId);
        return Result.ok("操作成功");
    }
}

