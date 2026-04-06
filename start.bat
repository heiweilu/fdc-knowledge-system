@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo   柔直仿真 AI 辅助知识系统
echo   MMC两端柔直系统仿真辅助平台
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 创建虚拟环境（如不存在）
if not exist ".venv" (
    echo [信息] 首次运行，正在创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查依赖是否已安装，未安装则安装
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装依赖...
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)

REM 检查 API Key
if "!DASHSCOPE_API_KEY!"=="" (
    echo.
    echo [提示] 未检测到 DASHSCOPE_API_KEY 环境变量
    set /p "DASHSCOPE_API_KEY=请输入你的通义千问 API Key: "
)
if "!DASHSCOPE_API_KEY!"=="" (
    echo [警告] 未输入 API Key，AI 功能将不可用
) else (
    echo [信息] API Key 已配置
)

echo.
echo [启动] 服务地址: http://localhost:8080
echo [提示] 关闭此窗口即可停止服务
echo.

REM 延迟2秒后自动打开浏览器
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8080"

REM 禁用 main.py 内部自动开页，避免重复弹出两个页面
set "AUTO_OPEN_BROWSER=0"

python main.py
if %errorlevel% neq 0 (
    echo.
    echo [!] 服务异常退出，请查看以上错误信息。
    pause
)
