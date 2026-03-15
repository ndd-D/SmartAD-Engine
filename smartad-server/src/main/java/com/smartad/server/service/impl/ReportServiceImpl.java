package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartad.server.dto.request.ChannelAdReportRequest;
import com.smartad.server.entity.SmartadReport;
import com.smartad.server.entity.SmartadStrategy;
import com.smartad.server.mapper.SmartadReportMapper;
import com.smartad.server.mapper.SmartadStrategyMapper;
import com.smartad.server.service.ReportService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReportServiceImpl implements ReportService {

    private final SmartadReportMapper reportMapper;
    private final SmartadStrategyMapper strategyMapper;

    @Override
    public Map<String, Object> getReportList(Integer page, Integer pageSize, String strategyId,
                                              String channel, String startDate, String endDate) {
        LambdaQueryWrapper<SmartadReport> wrapper = new LambdaQueryWrapper<SmartadReport>()
                .orderByDesc(SmartadReport::getReportDate);

        if (strategyId != null && !strategyId.trim().isEmpty()) {
            wrapper.eq(SmartadReport::getStrategyId, strategyId.trim());
        }
        if (channel != null && !channel.trim().isEmpty()) {
            wrapper.eq(SmartadReport::getChannel, channel.trim());
        }
        if (startDate != null && !startDate.isEmpty()) {
            wrapper.ge(SmartadReport::getReportDate, LocalDate.parse(startDate));
        }
        if (endDate != null && !endDate.isEmpty()) {
            wrapper.le(SmartadReport::getReportDate, LocalDate.parse(endDate));
        }

        com.baomidou.mybatisplus.core.metadata.IPage<SmartadReport> pageResult =
                reportMapper.selectPage(new Page<>(page, pageSize), wrapper);

        List<Map<String, Object>> records = new ArrayList<>();
        for (SmartadReport r : pageResult.getRecords()) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("id", r.getId());
            row.put("strategyId", r.getStrategyId());
            row.put("crowdTag", r.getCrowdTag());
            row.put("channel", r.getChannel());
            row.put("reportDate", r.getReportDate() != null ? r.getReportDate().toString() : "");
            row.put("impressions", r.getImpressions());
            row.put("clicks", r.getClicks());
            row.put("ctr", r.getCtr());
            row.put("conversions", r.getConversions());
            row.put("cost", r.getCost());
            row.put("roi", r.getRoi());
            row.put("updatedAt", r.getUpdatedAt() != null ? r.getUpdatedAt().toString() : "");
            records.add(row);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("records", records);
        result.put("total", pageResult.getTotal());
        result.put("page", page);
        result.put("pageSize", pageSize);
        return result;
    }

    @Override
    public Map<String, Object> getAdReport(String strategyId, String startTime, String endTime) {
        LambdaQueryWrapper<SmartadReport> wrapper = new LambdaQueryWrapper<SmartadReport>()
                .eq(SmartadReport::getStrategyId, strategyId)
                .orderByAsc(SmartadReport::getReportDate);

        if (startTime != null && !startTime.isEmpty()) wrapper.ge(SmartadReport::getReportDate, LocalDate.parse(startTime));
        if (endTime != null && !endTime.isEmpty()) wrapper.le(SmartadReport::getReportDate, LocalDate.parse(endTime));

        List<SmartadReport> reports = reportMapper.selectList(wrapper);

        long totalImpressions = reports.stream().mapToLong(r -> r.getImpressions() == null ? 0 : r.getImpressions()).sum();
        long totalClicks = reports.stream().mapToLong(r -> r.getClicks() == null ? 0 : r.getClicks()).sum();
        long totalConversions = reports.stream().mapToLong(r -> r.getConversions() == null ? 0 : r.getConversions()).sum();
        BigDecimal totalCost = reports.stream().map(r -> r.getCost() == null ? BigDecimal.ZERO : r.getCost())
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        BigDecimal avgRoi = reports.isEmpty() ? BigDecimal.ZERO :
                reports.stream().map(r -> r.getRoi() == null ? BigDecimal.ZERO : r.getRoi())
                        .reduce(BigDecimal.ZERO, BigDecimal::add)
                        .divide(BigDecimal.valueOf(reports.size()), 2, RoundingMode.HALF_UP);

        double ctr = totalImpressions == 0 ? 0 : (double) totalClicks / totalImpressions;
        double cvr = totalClicks == 0 ? 0 : (double) totalConversions / totalClicks;

        List<Map<String, Object>> dateList = new ArrayList<>();
        for (SmartadReport r : reports) {
            Map<String, Object> day = new LinkedHashMap<>();
            day.put("date", r.getReportDate() != null ? r.getReportDate().toString() : "");
            day.put("impressions", r.getImpressions());
            day.put("clicks", r.getClicks());
            day.put("cost", r.getCost());
            day.put("roi", r.getRoi());
            dateList.add(day);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("strategyId", strategyId);
        result.put("impressions", totalImpressions);
        result.put("clicks", totalClicks);
        result.put("ctr", String.format("%.4f", ctr));
        result.put("conversions", totalConversions);
        result.put("cvr", String.format("%.4f", cvr));
        result.put("cost", totalCost);
        result.put("roi", avgRoi);
        result.put("dateList", dateList);
        return result;
    }

    @Override
    public Map<String, Object> getRealTimeData(String strategyId) {
        SmartadReport todayReport = reportMapper.selectOne(
                new LambdaQueryWrapper<SmartadReport>()
                        .eq(SmartadReport::getStrategyId, strategyId)
                        .eq(SmartadReport::getReportDate, LocalDate.now())
        );

        SmartadStrategy strategy = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getStrategyId, strategyId)
        );

        Map<String, Object> result = new LinkedHashMap<>();
        if (todayReport != null) {
            double costRate = (strategy != null && strategy.getBudgetDay() != null
                    && strategy.getBudgetDay().compareTo(BigDecimal.ZERO) > 0)
                    ? todayReport.getCost().doubleValue() / strategy.getBudgetDay().doubleValue()
                    : 0;
            result.put("cost", todayReport.getCost());
            result.put("impressions", todayReport.getImpressions());
            result.put("clicks", todayReport.getClicks());
            result.put("conversions", todayReport.getConversions());
            result.put("ctr", todayReport.getCtr());
            result.put("roi", todayReport.getRoi());
            result.put("costRate", String.format("%.4f", costRate));
        } else {
            result.put("cost", 0);
            result.put("impressions", 0);
            result.put("clicks", 0);
            result.put("conversions", 0);
            result.put("ctr", 0);
            result.put("roi", 0);
            result.put("costRate", 0);
        }
        return result;
    }

    @Override
    public Map<String, Object> getHistoryReport(String crowdTag, String channel) {
        SmartadReportMapper.HistoryAvg avg = reportMapper.queryHistoryAvg(crowdTag, channel);

        BigDecimal avgCtr         = avg != null && avg.getAvgClickRate()   != null ? avg.getAvgClickRate()   : new BigDecimal("0.050");
        BigDecimal avgConvertRate = avg != null && avg.getAvgConvertRate() != null ? avg.getAvgConvertRate() : new BigDecimal("0.045");
        BigDecimal avgRoi         = avg != null && avg.getAvgRoi()         != null ? avg.getAvgRoi()         : new BigDecimal("2.0");

        BigDecimal suggestBid = avgCtr.multiply(new BigDecimal("15")).setScale(2, RoundingMode.HALF_UP);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("avgClickRate", avgCtr);
        result.put("avgConvertRate", avgConvertRate);
        result.put("avgBidPrice", suggestBid);
        result.put("suggestBid", suggestBid);
        result.put("suggestTime", "08:00-23:00");
        return result;
    }

    @Override
    public void receiveChannelReport(ChannelAdReportRequest request) {
        log.info("收到渠道数据回传: adId={}, channel={}, impressions={}, clicks={}, cost={}",
                request.getAdId(), request.getChannel(),
                request.getExpose(), request.getClick(), request.getCost());

        // 根据 channelAdId 找到对应策略
        SmartadStrategy strategy = strategyMapper.selectOne(
                new LambdaQueryWrapper<SmartadStrategy>()
                        .eq(SmartadStrategy::getChannelAdId, request.getAdId())
        );
        if (strategy == null) {
            log.warn("渠道数据回传：未找到对应策略，adId={}", request.getAdId());
            return;
        }

        LocalDate today = LocalDate.now();
        SmartadReport report = reportMapper.selectOne(
                new LambdaQueryWrapper<SmartadReport>()
                        .eq(SmartadReport::getStrategyId, strategy.getStrategyId())
                        .eq(SmartadReport::getReportDate, today)
        );

        long impressions = request.getExpose() != null ? request.getExpose() : 0L;
        long clicks = request.getClick() != null ? request.getClick() : 0L;
        long conversions = request.getConvert() != null ? request.getConvert() : 0L;
        BigDecimal cost = request.getCost() != null ? request.getCost() : BigDecimal.ZERO;
        BigDecimal roi = request.getRoi() != null ? request.getRoi() : BigDecimal.ZERO;
        BigDecimal ctr = impressions > 0
                ? BigDecimal.valueOf((double) clicks / impressions).setScale(4, RoundingMode.HALF_UP)
                : BigDecimal.ZERO;

        if (report == null) {
            report = new SmartadReport();
            report.setStrategyId(strategy.getStrategyId());
            report.setCrowdTag(strategy.getCrowdTag());
            report.setChannel(strategy.getChannel());
            report.setReportDate(today);
            report.setImpressions(impressions);
            report.setClicks(clicks);
            report.setCtr(ctr);
            report.setConversions((int) conversions);
            report.setCost(cost);
            report.setRoi(roi);
            reportMapper.insert(report);
            log.info("渠道数据回传：新建今日报表记录, strategyId={}", strategy.getStrategyId());
        } else {
            // 累加数据
            report.setImpressions((report.getImpressions() == null ? 0 : report.getImpressions()) + impressions);
            report.setClicks((report.getClicks() == null ? 0 : report.getClicks()) + clicks);
            report.setConversions((report.getConversions() == null ? 0 : report.getConversions()) + (int) conversions);
            report.setCost(report.getCost().add(cost));
            report.setRoi(roi); // ROI 取最新值
            long totalImpr = report.getImpressions();
            long totalClk = report.getClicks();
            report.setCtr(totalImpr > 0
                    ? BigDecimal.valueOf((double) totalClk / totalImpr).setScale(4, RoundingMode.HALF_UP)
                    : BigDecimal.ZERO);
            reportMapper.updateById(report);
            log.info("渠道数据回传：更新今日报表记录, strategyId={}", strategy.getStrategyId());
        }
    }

    @Override
    public List<Map<String, Object>> getStrategyReport(String strategyId, Integer days) {
        int queryDays = (days != null && days > 0) ? days : 7;
        List<SmartadReport> reports = reportMapper.selectList(
                new LambdaQueryWrapper<SmartadReport>()
                        .eq(SmartadReport::getStrategyId, strategyId)
                        .ge(SmartadReport::getReportDate, LocalDate.now().minusDays(queryDays))
                        .orderByAsc(SmartadReport::getReportDate)
        );

        List<Map<String, Object>> result = new ArrayList<>();
        for (SmartadReport r : reports) {
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("reportDate", r.getReportDate() != null ? r.getReportDate().toString() : "");
            row.put("impressions", r.getImpressions());
            row.put("clicks", r.getClicks());
            row.put("ctr", r.getCtr());
            row.put("conversions", r.getConversions());
            row.put("cost", r.getCost());
            row.put("roi", r.getRoi());
            result.add(row);
        }
        return result;
    }
}
