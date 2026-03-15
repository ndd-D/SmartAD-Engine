package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.smartad.server.common.BusinessException;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadCommand;
import com.smartad.server.entity.SmartadStrategy;
import com.smartad.server.mapper.SmartadCommandMapper;
import com.smartad.server.mapper.SmartadStrategyMapper;
import com.smartad.server.service.StrategyService;
import com.smartad.server.util.IdGenerator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 策略状态枚举（英文，与前端、数据库一致）：
 * pending          - AI生成，等待人工普通确认
 * risk_pending     - AI生成高风险，等待人工高风险确认
 * running          - 投放中
 * paused           - 已暂停
 * offline          - 已下线
 * rejected         - 已拒绝
 * timeout          - 超时失效（高风险2h未确认）
 */

@Slf4j
@Service
@RequiredArgsConstructor
public class StrategyServiceImpl implements StrategyService {

    private final SmartadStrategyMapper strategyMapper;
    private final SmartadCommandMapper commandMapper;
    private final ObjectMapper objectMapper;

    @Override
    public SmartadStrategy getStrategyInfo(String strategyId) {
        SmartadStrategy strategy = getByStrategyId(strategyId);
        return strategy;
    }

    @Override
    @Transactional
    public Map<String, Object> confirmStrategy(StrategyConfirmRequest request) {
        SmartadStrategy strategy = getByStrategyId(request.getStrategyId());

        if ("编辑".equals(request.getOperateType())) {
            // 仅允许编辑 budgetDay 和 bidPrice
            if (request.getEditData() != null) {
                if (request.getEditData().getBudgetDay() != null) {
                    strategy.setBudgetDay(new java.math.BigDecimal(request.getEditData().getBudgetDay()));
                }
                if (request.getEditData().getBidPrice() != null) {
                    strategy.setBidPrice(request.getEditData().getBidPrice().intValue());
                }
            }
            strategyMapper.updateById(strategy);
        } else if ("上线".equals(request.getOperateType())) {
            strategy.setStatus("running");
            strategyMapper.updateById(strategy);
            // 上线后异步触发渠道广告创建（Mock）
            log.info("策略上线，触发渠道广告创建: strategyId={}, channel={}", strategy.getStrategyId(), strategy.getChannel());
        } else {
            throw new BusinessException("operateType参数错误，仅支持：上线/编辑");
        }

        Map<String, Object> result = new HashMap<>();
        result.put("strategyId", strategy.getStrategyId());
        result.put("status", strategy.getStatus());
        return result;
    }

    @Override
    @Transactional
    public Map<String, Object> riskConfirm(RiskConfirmRequest request) {
        SmartadStrategy strategy = getByStrategyId(request.getStrategyId());

        if (!"risk_pending".equals(strategy.getStatus())) {
            throw new BusinessException("策略当前状态不是高风险待确认（risk_pending），无需该流程");
        }

        LocalDateTime now = LocalDateTime.now();
        String newStatus;
        if ("同意".equals(request.getConfirmResult())) {
            newStatus = "pending"; // 进入普通待确认，等待上线操作
        } else if ("拒绝".equals(request.getConfirmResult())) {
            newStatus = "rejected";
        } else {
            throw new BusinessException("confirmResult参数错误，仅支持：同意/拒绝");
        }

        strategy.setStatus(newStatus);
        strategyMapper.updateById(strategy);

        Map<String, Object> result = new HashMap<>();
        result.put("strategyId", strategy.getStrategyId());
        result.put("status", newStatus);
        result.put("confirmTime", now.toString());
        return result;
    }

    @Override
    public Map<String, String> stopStrategy(StrategyStopRequest request) {
        SmartadStrategy strategy = getByStrategyId(request.getStrategyId());

        String newStatus;
        if ("暂停".equals(request.getOperateType())) {
            newStatus = "paused";
        } else if ("下线".equals(request.getOperateType())) {
            newStatus = "offline";
        } else {
            throw new BusinessException("operateType参数错误，仅支持：暂停/下线");
        }

        strategy.setStatus(newStatus);
        strategyMapper.updateById(strategy);

        Map<String, String> result = new HashMap<>();
        result.put("strategyId", strategy.getStrategyId());
        result.put("status", newStatus);
        return result;
    }

    @Override
    public IPage<SmartadStrategy> listStrategies(Integer pageNum, Integer pageSize, String status, String channel) {
        Page<SmartadStrategy> page = new Page<>(pageNum, pageSize);
        LambdaQueryWrapper<SmartadStrategy> wrapper = new LambdaQueryWrapper<SmartadStrategy>()
                .orderByDesc(SmartadStrategy::getCreatedAt);
        if (StringUtils.hasText(status)) {
            wrapper.eq(SmartadStrategy::getStatus, status);
        }
        if (StringUtils.hasText(channel)) {
            wrapper.eq(SmartadStrategy::getChannel, channel.trim());
        }
        return strategyMapper.selectPage(page, wrapper);
    }

    @Override
    @Transactional
    public Map<String, String> syncStrategyFromAi(AiStrategySyncRequest request) {
        // ✅ 幂等检查：同一commandId已经有策略，直接返回
        SmartadStrategy existing = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getCommandId, request.getCommandId())
        );
        if (existing != null) {
            log.warn("重复同步，commandId={} 已关联策略={}", request.getCommandId(), existing.getStrategyId());
            Map<String, String> dup = new HashMap<>();
            dup.put("strategyId", existing.getStrategyId());
            dup.put("status", existing.getStatus());
            return dup;
        }

        // 生成策略ID
        long seq = strategyMapper.countToday() + 1;
        String strategyId = IdGenerator.generate("STR", seq);

        SmartadStrategy strategy = new SmartadStrategy();
        strategy.setStrategyId(strategyId);
        strategy.setCommandId(request.getCommandId());

        // channel：取第一个渠道
        if (request.getChannels() != null && !request.getChannels().isEmpty()) {
            strategy.setChannel(request.getChannels().get(0));
        }

        strategy.setBudgetDay(request.getBudgetDay() != null ? new java.math.BigDecimal(request.getBudgetDay().toString()) : null);
        strategy.setCrowdTag(request.getCrowdTag());
        strategy.setBidPrice(request.getBidPrice() != null ? request.getBidPrice().intValue() : null);

        // ✅ 风险等级决定初始状态：高风险→risk_pending，普通→pending
        String riskLevel = request.getRiskLevel() != null ? request.getRiskLevel() : "普通";
        String initialStatus = "高风险".equals(riskLevel) ? "risk_pending" : "pending";
        strategy.setStatus(initialStatus);

        strategyMapper.insert(strategy);

        // 更新指令表关联的strategyId
        SmartadCommand command = commandMapper.selectOne(
                new LambdaQueryWrapper<SmartadCommand>()
                        .eq(SmartadCommand::getCommandId, request.getCommandId())
        );
        if (command != null) {
            command.setStrategyId(strategyId);
            command.setStatus("已生成策略");
            commandMapper.updateById(command);
        }

        log.info("AI同步策略成功: strategyId={}, status={}", strategyId, initialStatus);

        Map<String, String> result = new HashMap<>();
        result.put("strategyId", strategyId);
        result.put("status", initialStatus);
        return result;
    }

    @Override
    public void adjustStrategy(AiStrategyAdjustRequest request) {
        SmartadStrategy strategy = getByStrategyId(request.getStrategyId());

        switch (request.getAdjustType()) {
            case "bidPrice" -> strategy.setBidPrice(request.getNewValue().intValue());
            case "budgetDay" -> strategy.setBudgetDay(request.getNewValue());
            case "runTime" -> log.info("runTime调整由AI直接传入新值: {}", request.getNewValue());
            default -> throw new BusinessException("adjustType不支持: " + request.getAdjustType());
        }

        strategyMapper.updateById(strategy);
        log.info("AI调整策略参数: strategyId={}, type={}, old={}, new={}, reason={}",
                request.getStrategyId(), request.getAdjustType(),
                request.getOldValue(), request.getNewValue(), request.getReason());
    }

    @Override
    public List<SmartadStrategy> getActiveStrategies() {
        return strategyMapper.selectList(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getStatus, "running")
                        .orderByAsc(SmartadStrategy::getCreatedAt)
        );
    }

    @Override
    public Map<String, String> evaluateStrategy(AiStrategyEvaluateRequest request) {
        // 将评估分数和调整结果回写到策略表
        SmartadStrategy strategy = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getStrategyId, request.getStrategyId())
        );
        if (strategy != null) {
            strategy.setAiReason(request.getEvaluateReason());
            strategyMapper.updateById(strategy);
        }

        // 生成 caseId（格式：CASE+日期+序号，简化实现）
        String caseId = "CASE" + System.currentTimeMillis();
        log.info("AI评估结果入库: strategyId={}, result={}, caseId={}, reason={}",
                request.getStrategyId(), request.getEvaluateResult(), caseId, request.getEvaluateReason());

        Map<String, String> result = new HashMap<>();
        result.put("caseId", caseId);
        return result;
    }

    private SmartadStrategy getByStrategyId(String strategyId) {
        SmartadStrategy strategy = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getStrategyId, strategyId)
        );
        if (strategy == null) {
            throw new BusinessException("策略不存在: " + strategyId);
        }
        return strategy;
    }
}
