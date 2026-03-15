package com.smartad.server.service;

import com.smartad.server.dto.request.LoginRequest;
import com.smartad.server.dto.response.LoginResponse;

public interface UserService {
    LoginResponse login(LoginRequest request);
}
