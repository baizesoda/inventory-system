@echo off
REM ============== Windows 一键启动脚本 ==============
cd /d "%~dp0\.."

echo [1/5] 检查 Python 环境...
where python >nul 2>nul
if errorlevel 1 (
    echo 未检测到 python, 请先安装
    pause
    exit /b 1
)

echo [2/5] 创建虚拟环境(若不存在)...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat

echo [3/5] 安装依赖...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/5] 执行数据库迁移...
python manage.py migrate --noinput

echo [5/5] 初始化演示数据(若数据库为空)...
python manage.py init_demo

echo ============================================
echo  开发模式启动, 访问 http://127.0.0.1:8000
echo ============================================
python manage.py runserver
pause
