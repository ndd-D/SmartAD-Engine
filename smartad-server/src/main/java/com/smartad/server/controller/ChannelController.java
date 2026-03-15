package com.smartad.server.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.smartad.server.common.Result;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadStrategy;
import com.smartad.server.mapper.SmartadStrategyMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Slf4j
@Tag(name = "渠道接口（模拟）")
@RestController
@RequestMapping("/api/channel")
@RequiredArgsConstructor
public class ChannelController {

    private final SmartadStrategyMapper strategyMapper;

    @Operation(summary = "渠道广告创建（Mock实现，回写channelAdId）")
    @PostMapping("/ad/create")
    public Result<Map<String, String>> createAd(@Valid @RequestBody ChannelAdCreateRequest request) {
        log.info("模拟创建渠道广告: strategyId={}, channel={}", request.getStrategyId(), request.getChannel());

        // 生成 Mock 广告ID（真实场景调用渠道 SDK）
        String mockAdId = "AD_" + request.getChannel().toUpperCase() + "_" + System.currentTimeMillis();

        // ✅ 回写 channelAdId 到策略表，供数据回传时关联
        SmartadStrategy strategy = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getStrategyId, request.getStrategyId())
        );
        if (strategy != null) {
            strategy.setChannelAdId(mockAdId);
            strategy.setStatus("running");
            strategyMapper.updateById(strategy);
            log.info("策略已上线，channelAdId={}", mockAdId);
        }

        return Result.success("广告创建成功", Map.of("adId", mockAdId, "status", "投放中"));
    }

    @Operation(summary = "渠道广告暂停/下线（Mock）")
    @PostMapping("/ad/operate")
    public Result<Map<String, String>> operateAd(@RequestBody Map<String, String> body) {
        String adId = body.get("adId");
        String operateType = body.get("operateType");
        String status = "pause".equals(operateType) ? "已暂停" : "已下线";
        log.info("模拟操作渠道广告: adId={}, operate={}", adId, operateType);
        return Result.success("操作成功", Map.of("adId", adId, "status", status));
    }

    @Operation(summary = "渠道广告数据回传（写入report表）")
    @PostMapping("/ad/report")
    public Result<Void> reportData(@Valid @RequestBody ChannelAdReportRequest request) {
        log.info("渠道数据回传: adId={}, expose={}, click={}", request.getAdId(), request.getExpose(), request.getClick());
        // 由 ReportService.receiveChannelReport 处理数据写入
        return Result.success("数据同步成功", null);
    }
}

