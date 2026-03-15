package com.smartad.server.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadStrategy;

import java.util.List;
import java.util.Map;

public interface StrategyService {

    /** 查询策略详情 */
    SmartadStrategy getStrategyInfo(String strategyId);

    /** 策略确认上线/编辑 */
    Map<String, Object> confirmStrategy(StrategyConfirmRequest request);

    /** 高风险策略人工确认 */
    Map<String, Object> riskConfirm(RiskConfirmRequest request);

    /** 策略暂停/下线 */
    Map<String, String> stopStrategy(StrategyStopRequest request);

    /** 策略分页列表 */
    IPage<SmartadStrategy> listStrategies(Integer pageNum, Integer pageSize, String status, String channel);

    /** AI同步策略到Java后端 */
    Map<String, String> syncStrategyFromAi(AiStrategySyncRequest request);

    /** AI自动调整策略参数 */
    void adjustStrategy(AiStrategyAdjustRequest request);

    /** AI获取所有投放中策略（status=running） */
    List<SmartadStrategy> getActiveStrategies();

    /** AI上报评估结果，持久化并返回caseId */
    Map<String, String> evaluateStrategy(AiStrategyEvaluateRequest request);
}

