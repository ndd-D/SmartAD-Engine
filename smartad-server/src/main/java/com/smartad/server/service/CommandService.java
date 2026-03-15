package com.smartad.server.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadCommand;

import java.util.List;
import java.util.Map;

public interface CommandService {

    /** 前端下发指令 */
    Map<String, String> submitCommand(CommandRequest request);

    /** 查询指令执行状态 */
    Map<String, Object> getCommandStatus(String commandId);

    /** 前端回复AI提问 */
    Map<String, String> replyCommand(CommandReplyRequest request);

    /** AI获取待处理指令列表 */
    List<SmartadCommand> getPendingCommandsForAi(String status);

    /** AI更新指令状态 */
    void updateCommandByAi(AiCommandUpdateRequest request);
}
