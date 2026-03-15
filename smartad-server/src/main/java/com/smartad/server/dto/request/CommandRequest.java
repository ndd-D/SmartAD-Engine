package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class CommandRequest {

    /** 兼容 commandText 和 command 两种字段名 */
    @NotBlank(message = "指令内容不能为空")
    private String commandText;

    /** 可选，不传时后端自动处理 */
    private Long userId;

    /** 兼容旧字段名 */
    public String getCommand() {
        return commandText;
    }
}
