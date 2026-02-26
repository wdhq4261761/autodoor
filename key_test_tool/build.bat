@echo off
chcp 65001 >nul
echo ========================================
echo   Windows按键测试工具 - 打包脚本
echo ========================================
echo.

cd /d "%~dp0key_test_tool"

echo [1/3] 检查依赖...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo   安装 pyinstaller...
    pip install pyinstaller -q
)

echo [2/3] 开始打包...
echo   这可能需要几分钟，请耐心等待...
echo.

pyinstaller key_test_tool.spec --clean --noconfirm

if %errorlevel% neq 0 (
    echo.
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.

if exist "dist\KeyTestTool\KeyTestTool.exe" (
    echo 成功！exe文件位于:
    echo   %~dp0key_test_tool\dist\KeyTestTool\KeyTestTool.exe
    echo.
    echo 可以将 dist\KeyTestTool 文件夹整体复制到其他电脑使用
    echo 无需安装任何运行环境
    start explorer /select,"%~dp0key_test_tool\dist\KeyTestTool\KeyTestTool.exe"
) else (
    echo [错误] 未找到exe文件
)

echo.
pause
