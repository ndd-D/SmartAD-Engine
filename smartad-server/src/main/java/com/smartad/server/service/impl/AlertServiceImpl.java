package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.smartad.server.dto.request.AiAlertPushRequest;
import com.smartad.server.entity.SmartadAlert;
import com.smartad.server.mapper.SmartadAlertMapper;
import com.smartad.server.service.AlertService;
import com.smartad.server.util.IdGenerator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class AlertServiceImpl implements AlertService {

    private final SmartadAlertMapper alertMapper;

    @Override
    public IPage<SmartadAlert> listAlerts(Integer page, Integer pageSize, String status, String alertLevel) {
        LambdaQueryWrapper<SmartadAlert> wrapper = new LambdaQueryWrapper<SmartadAlert>()
                .orderByDesc(SmartadAlert::getCreatedAt);
        if (StringUtils.hasText(status)) {
            wrapper.eq(SmartadAlert::getStatus, status);
        }
        if (StringUtils.hasText(alertLevel)) {
            wrapper.eq(SmartadAlert::getAlertLevel, alertLevel);
        }
        return alertMapper.selectPage(new Page<>(page, pageSize), wrapper);
    }

    @Override
    public void pushAlert(AiAlertPushRequest request) {
        long seq = alertMapper.countToday() + 1;
        String alertId = IdGenerator.generate("ALT", seq);

        SmartadAlert alert = new SmartadAlert();
        alert.setAlertId(alertId);
        alert.setAlertMessage(request.getAlertContent());
        alert.setAlertType(request.getAlertType());
        alert.setStrategyId(request.getRelatedId());
        alert.setStatus("active");
        alertMapper.insert(alert);

        log.warn("系统告警: type={}, content={}, relatedId={}", request.getAlertType(), request.getAlertContent(), request.getRelatedId());
    }

    @Override
    public void confirmAlert(String alertId) {
        alertMapper.update(null, new LambdaUpdateWrapper<SmartadAlert>()
                .eq(SmartadAlert::getAlertId, alertId)
                .set(SmartadAlert::getStatus, "confirmed")
                .set(SmartadAlert::getConfirmedAt, LocalDateTime.now())
        );
    }
}
