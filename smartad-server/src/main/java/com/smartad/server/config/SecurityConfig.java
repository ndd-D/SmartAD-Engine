package com.smartad.server.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 仅注册BCryptPasswordEncoder Bean
 * Spring Security自动配置已在启动类上通过exclude禁用
 * 鉴权由自定义 AuthInterceptor（Spring MVC拦截器）统一负责
 */
@Configuration
public class SecurityConfig {

    @Bean
    public BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}


