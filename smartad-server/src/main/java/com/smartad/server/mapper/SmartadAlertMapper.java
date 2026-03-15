package com.smartad.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartad.server.entity.SmartadAlert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface SmartadAlertMapper extends BaseMapper<SmartadAlert> {

    @Select("SELECT COUNT(*) FROM smartad_alert WHERE DATE(created_at) = CURDATE()")
    long countToday();
}
