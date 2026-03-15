package com.smartad.server.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.smartad.server.dto.request.AiAlertPushRequest;
import com.smartad.server.entity.SmartadAlert;

public interface AlertService {
    IPage<SmartadAlert> listAlerts(Integer page, Integer pageSize, String status, String alertLevel);
    void pushAlert(AiAlertPushRequest request);
    void confirmAlert(String alertId);
}

