package com.smartad.server.config;

import com.smartad.server.common.BusinessException;
import com.smartad.server.util.JwtUtil;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 认证拦截器（用户token + AI token双通道）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthInterceptor implements HandlerInterceptor {

    private final JwtUtil jwtUtil;

    @Value("${smartad.ai-token}")
    private String aiToken;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        String requestURI = request.getRequestURI();
        log.debug("拦截请求: {}", requestURI);

        // AI接口：校验ai-token
        if (requestURI.startsWith("/api/ai/") || requestURI.startsWith("/api/channel/") || requestURI.startsWith("/api/data/")) {
            String token = request.getHeader("ai-token");
            if (!aiToken.equals(token)) {
                throw new BusinessException(401, "AI Token无效或未提供");
            }
            return true;
        }

        // 用户接口：校验JWT token
        String token = request.getHeader("token");
        if (token == null || token.isEmpty()) {
            throw new BusinessException(401, "未授权，请先登录");
        }
        if (!jwtUtil.isValid(token)) {
            throw new BusinessException(401, "Token已过期或无效，请重新登录");
        }

        // 将userId存入request attribute，方便后续使用
        Long userId = jwtUtil.getUserId(token);
        request.setAttribute("currentUserId", userId);
        return true;
    }
}
