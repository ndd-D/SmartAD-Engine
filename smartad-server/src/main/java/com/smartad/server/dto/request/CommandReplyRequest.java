package com.smartad.server.dto.request;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CommandReplyRequest {

    @NotBlank(message = "commandId不能为空")
    private String commandId;

    /** 前端传 replyText，兼容 replyContent */
    @NotBlank(message = "回复内容不能为空")
    private String replyText;

    /** 兼容旧字段名 */
    public String getReplyContent() {
        return replyText;
    }
}
