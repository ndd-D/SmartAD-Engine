package com.smartad.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartad.server.entity.SmartadUser;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface SmartadUserMapper extends BaseMapper<SmartadUser> {
}
