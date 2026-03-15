@echo off
chcp 65001 > nul
echo.
echo ============================================================
echo   SmartAD Agent - 快速测试启动脚本
echo ============================================================
echo.

:: 定位 Python（优先使用项目内 venv，其次 E:\develop\python311）
set PYTHON=
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "E:\develop\python311\python.exe" (
    set PYTHON=E:\develop\python311\python.exe
) else (
    set PYTHON=python
)
echo [INFO] 使用 Python: %PYTHON%
echo.

:: 检查参数
if "%1"=="install" goto INSTALL
if "%1"=="test" goto TEST
if "%1"=="test-llm" goto TEST_LLM
if "%1"=="run" goto RUN
goto HELP

:INSTALL
echo [STEP 1] 安装依赖...
%PYTHON% -m pip install langchain langchain-core langchain-openai cachetools fastapi uvicorn httpx pydantic pydantic-settings python-dotenv loguru apscheduler
echo.
echo [DONE] 依赖安装完成，运行 start.bat test 进行测试
goto END

:TEST
echo [STEP] 运行快速验证（不需要 LLM，1秒内完成）...
echo.
%PYTHON% test_agent.py T1 T8 T9 T10
echo.
echo 提示: 运行 start.bat test-llm 可测试 LLM 链路（需要联网）
goto END

:TEST_LLM
echo [STEP] 运行完整测试（包含 LLM 调用，约 30-60 秒）...
echo.
%PYTHON% test_agent.py
goto END

:RUN
echo [STEP] 启动 SmartAD Agent 服务...
echo.
echo 注意: 确保 Java 后端已在 8081 端口运行
echo       日志输出到 logs/smartad-agent.log
echo.
%PYTHON% main.py
goto END

:HELP
echo 用法:
echo   start.bat install     安装/更新所有依赖
echo   start.bat test        快速验证（不需要LLM，离线可用）
echo   start.bat test-llm    完整测试（含LLM链路调用）
echo   start.bat run         启动 Agent 服务
echo.
echo 示例:
echo   start.bat install     ^<-- 首次使用先安装依赖
echo   start.bat test        ^<-- 验证代码结构正确
echo   start.bat test-llm    ^<-- 验证 AI 链路联通
echo   start.bat run         ^<-- 启动服务

:END
echo.
