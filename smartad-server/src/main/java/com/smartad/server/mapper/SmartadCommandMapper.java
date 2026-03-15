package com.smartad.server.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartad.server.entity.SmartadCommand;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface SmartadCommandMapper extends BaseMapper<SmartadCommand> {

    /**
     * 查询今日最大序号（用于生成commandId）
     */
    @Select("SELECT COUNT(*) FROM smartad_command WHERE DATE(created_at) = CURDATE()")
    long countToday();
}
