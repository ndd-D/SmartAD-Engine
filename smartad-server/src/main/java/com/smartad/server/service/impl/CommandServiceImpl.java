package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.smartad.server.common.BusinessException;
import com.smartad.server.dto.request.*;
import com.smartad.server.entity.SmartadCommand;
import com.smartad.server.mapper.SmartadCommandMapper;
import com.smartad.server.service.CommandService;
import com.smartad.server.util.IdGenerator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class CommandServiceImpl implements CommandService {

    private final SmartadCommandMapper commandMapper;

    @Override
    public Map<String, String> submitCommand(CommandRequest request) {
        // 生成commandId：CMD + 今日序号
        long seq = commandMapper.countToday() + 1;
        String commandId = IdGenerator.generate("CMD", seq);

        SmartadCommand command = new SmartadCommand();
        command.setCommandId(commandId);
        command.setUserId(request.getUserId());
        command.setCommandText(request.getCommand());
        command.setStatus("待AI处理");
        commandMapper.insert(command);

        Map<String, String> result = new HashMap<>();
        result.put("commandId", commandId);
        result.put("status", "待AI处理");
        return result;
    }

    @Override
    public Map<String, Object> getCommandStatus(String commandId) {
        SmartadCommand command = getByCommandId(commandId);

        Map<String, Object> result = new HashMap<>();
        // 将中文状态映射为前端期望的英文状态
        String frontStatus = switch (command.getStatus()) {
            case "AI提问中" -> "waiting_reply";
            case "已生成策略" -> "completed";
            case "执行失败" -> "failed";
            default -> "processing"; // 待AI处理、处理中
        };
        result.put("commandId", commandId);
        result.put("status", frontStatus);
        result.put("strategyId", command.getStrategyId());
        result.put("failReason", command.getFailReason() == null ? "" : command.getFailReason());
        result.put("aiQuestion", command.getAiQuestion() == null ? "" : command.getAiQuestion());
        return result;
    }

    @Override
    public Map<String, String> replyCommand(CommandReplyRequest request) {
        SmartadCommand command = getByCommandId(request.getCommandId());

        if (!"AI提问中".equals(command.getStatus())) {
            throw new BusinessException("当前指令状态不是AI提问中，无需回复");
        }

        command.setReplyContent(request.getReplyContent());
        command.setReplyTime(LocalDateTime.now());
        command.setStatus("处理中");
        commandMapper.updateById(command);

        Map<String, String> result = new HashMap<>();
        result.put("commandId", request.getCommandId());
        result.put("status", "处理中");
        return result;
    }

    @Override
    public List<SmartadCommand> getPendingCommandsForAi(String status) {
        // 支持多状态：待AI处理,AI提问中
        if (status != null && status.contains(",")) {
            String[] statuses = status.split(",");
            return commandMapper.selectList(
                    new LambdaQueryWrapper<SmartadCommand>()
                            .in(SmartadCommand::getStatus, (Object[]) statuses)
                            .orderByAsc(SmartadCommand::getCreateTime)
            );
        }
        return commandMapper.selectList(
                new LambdaQueryWrapper<SmartadCommand>()
                        .eq(SmartadCommand::getStatus, status != null ? status : "待AI处理")
                        .orderByAsc(SmartadCommand::getCreateTime)
        );
    }

    @Override
    public void updateCommandByAi(AiCommandUpdateRequest request) {
        SmartadCommand command = getByCommandId(request.getCommandId());

        // 状态映射：AI上报"已完成" → 库里存"已生成策略"
        String newStatus = mapAiStatus(request.getStatus());
        command.setStatus(newStatus);

        if (request.getFailReason() != null) {
            command.setFailReason(request.getFailReason());
        }
        if (request.getAiQuestion() != null) {
            command.setAiQuestion(request.getAiQuestion());
        }
        commandMapper.updateById(command);
        log.info("AI更新指令状态: commandId={}, status={}", request.getCommandId(), newStatus);
    }

    private SmartadCommand getByCommandId(String commandId) {
        SmartadCommand command = commandMapper.selectOne(
                new LambdaQueryWrapper<SmartadCommand>()
                        .eq(SmartadCommand::getCommandId, commandId)
        );
        if (command == null) {
            throw new BusinessException("指令不存在: " + commandId);
        }
        return command;
    }

    private String mapAiStatus(String aiStatus) {
        return switch (aiStatus) {
            case "已完成" -> "已生成策略";
            case "处理失败" -> "执行失败";
            default -> aiStatus; // 处理中、AI提问中 直接映射
        };
    }
}
