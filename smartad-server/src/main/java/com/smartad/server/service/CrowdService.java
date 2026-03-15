package com.smartad.server.service;

import com.smartad.server.entity.SmartadCrowd;

import java.util.List;

public interface CrowdService {
    SmartadCrowd getCrowdInfo(String crowdTag);
    List<SmartadCrowd> listAllCrowds();
}

