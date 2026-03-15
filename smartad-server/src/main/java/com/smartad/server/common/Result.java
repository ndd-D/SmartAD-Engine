package com.smartad.server.common;

import lombok.Data;

/**
 * 统一响应封装
 */
@Data
public class Result<T> {

    private Integer code;
    private String msg;
    private T data;

    private Result(Integer code, String msg, T data) {
        this.code = code;
        this.msg = msg;
        this.data = data;
    }

    public static <T> Result<T> success(T data) {
        return new Result<>(200, "操作成功", data);
    }

    public static <T> Result<T> success(String msg, T data) {
        return new Result<>(200, msg, data);
    }

    public static Result<Void> ok(String msg) {
        return new Result<>(200, msg, null);
    }

    public static <T> Result<T> fail(String msg) {
        return new Result<>(500, msg, null);
    }

    public static <T> Result<T> fail(Integer code, String msg) {
        return new Result<>(code, msg, null);
    }

    public static <T> Result<T> unauthorized() {
        return new Result<>(401, "未授权，请先登录", null);
    }

    public static <T> Result<T> paramError(String msg) {
        return new Result<>(400, msg, null);
    }

    public static <T> Result<T> timeout() {
        return new Result<>(408, "接口超时，请稍后重试", null);
    }
}
