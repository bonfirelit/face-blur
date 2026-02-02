@echo off
REM ========================================
REM FaceBlur Pro Windows 打包脚本
REM ========================================

REM 设置版本号（修改这里来发布新版本）
set VERSION=1.0.0

REM 使用日期作为构建号
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
set BUILD_DATE=%mydate%

set RELEASE_NAME=FaceBlur-Pro-v%VERSION%-%BUILD_DATE%

echo ========================================
echo   FaceBlur Pro 打包工具 v%VERSION%
echo   构建日期: %BUILD_DATE%
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] 检查 Python 环境...
python --version

echo.
echo [2/5] 安装 PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [3/5] 安装项目依赖...
pip install -r ../requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [4/5] 开始打包 (这可能需要几分钟)...
pyinstaller build.spec

echo.
echo [5/5] 复制文件到发布目录...
if not exist "%RELEASE_NAME%" mkdir "%RELEASE_NAME%"
copy dist\FaceBlur-Pro.exe "%RELEASE_NAME%\" >nul
copy release_template\README_用户使用说明.md "%RELEASE_NAME%\使用说明.md" >nul 2>&1

REM 创建版本信息文件
echo FaceBlur Pro v%VERSION% > "%RELEASE_NAME%\版本信息.txt"
echo 构建日期: %BUILD_DATE% >> "%RELEASE_NAME%\版本信息.txt"
echo. >> "%RELEASE_NAME%\版本信息.txt"
echo 版本历史: >> "%RELEASE_NAME%\版本信息.txt"
echo - v%VERSION% (%BUILD_DATE%) >> "%RELEASE_NAME%\版本信息.txt"

REM 创建启动脚本
echo @echo off > "%RELEASE_NAME%\启动程序.bat"
echo title FaceBlur Pro >> release\启动程序.bat
echo echo 启动 FaceBlur Pro... >> release\启动程序.bat
echo echo. >> release\启动程序.bat
echo start "" "FaceBlur-Pro.exe" >> release\启动程序.bat

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 版本: v%VERSION%
echo 构建日期: %BUILD_DATE%
echo 发布文件位置: %CD%\%RELEASE_NAME%\
echo.
echo 下一步:
echo 1. 将 %RELEASE_NAME% 文件夹压缩成 ZIP
echo 2. 分发给用户
echo 3. 用户解压后双击 "启动程序.bat" 即可使用
echo.
pause
