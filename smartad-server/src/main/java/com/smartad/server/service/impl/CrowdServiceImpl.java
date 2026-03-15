package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.smartad.server.common.BusinessException;
import com.smartad.server.entity.SmartadCrowd;
import com.smartad.server.mapper.SmartadCrowdMapper;
import com.smartad.server.service.CrowdService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class CrowdServiceImpl implements CrowdService {

    private final SmartadCrowdMapper crowdMapper;

    @Override
    public SmartadCrowd getCrowdInfo(String crowdTag) {
        SmartadCrowd crowd = crowdMapper.selectOne(
                new LambdaQueryWrapper<SmartadCrowd>()
                        .eq(SmartadCrowd::getCrowdTag, crowdTag)
        );
        if (crowd == null) {
            throw new BusinessException("未找到人群画像数据: " + crowdTag);
        }
        return crowd;
    }

    @Override
    public List<SmartadCrowd> listAllCrowds() {
        return crowdMapper.selectList(new LambdaQueryWrapper<SmartadCrowd>()
                .orderByAsc(SmartadCrowd::getId));
    }
}

