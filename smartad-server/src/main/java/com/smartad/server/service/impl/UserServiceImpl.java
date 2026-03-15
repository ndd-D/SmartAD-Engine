package com.smartad.server.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.smartad.server.common.BusinessException;
import com.smartad.server.dto.request.LoginRequest;
import com.smartad.server.dto.response.LoginResponse;
import com.smartad.server.entity.SmartadUser;
import com.smartad.server.mapper.SmartadUserMapper;
import com.smartad.server.service.UserService;
import com.smartad.server.util.JwtUtil;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Slf4j
@Service
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final SmartadUserMapper userMapper;
    private final JwtUtil jwtUtil;
    private final BCryptPasswordEncoder passwordEncoder;

    @Override
    public LoginResponse login(LoginRequest request) {
        SmartadUser user = userMapper.selectOne(
                new LambdaQueryWrapper<SmartadUser>()
                        .eq(SmartadUser::getUsername, request.getUsername())
                        .eq(SmartadUser::getStatus, 1)
        );

        if (user == null) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new BusinessException(401, "用户名或密码错误");
        }

        // 更新最后登录时间
        user.setLastLoginTime(LocalDateTime.now());
        userMapper.updateById(user);

        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRole());

        return LoginResponse.builder()
                .token(token)
                .userId(user.getId())
                .nickname(user.getNickname())
                .role(user.getRole())
                .build();
    }
}
