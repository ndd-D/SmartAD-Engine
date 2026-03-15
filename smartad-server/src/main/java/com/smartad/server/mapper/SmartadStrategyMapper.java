package com.smartad.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartad.server.entity.SmartadStrategy;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface SmartadStrategyMapper extends BaseMapper<SmartadStrategy> {

    @Select("SELECT COUNT(*) FROM smartad_strategy WHERE DATE(created_at) = CURDATE()")
    long countToday();
}
