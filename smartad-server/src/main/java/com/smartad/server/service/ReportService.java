package com.smartad.server.service;

import com.smartad.server.entity.SmartadReport;

import java.util.List;
import java.util.Map;

public interface ReportService {

    /** 前端分页查询投放数据报表列表 */
    Map<String, Object> getReportList(Integer page, Integer pageSize, String strategyId,
                                       String channel, String startDate, String endDate);

    /** 前端查询投放数据报表（按策略汇总） */
    Map<String, Object> getAdReport(String strategyId, String startTime, String endTime);

    /** AI查询实时数据 */
    Map<String, Object> getRealTimeData(String strategyId);

    /** AI查询历史投放效果 */
    Map<String, Object> getHistoryReport(String crowdTag, String channel);

    /** 渠道数据回传 */
    void receiveChannelReport(com.smartad.server.dto.request.ChannelAdReportRequest request);

    /** AI获取策略近N天报表明细（用于评估） */
    List<Map<String, Object>> getStrategyReport(String strategyId, Integer days);
}


