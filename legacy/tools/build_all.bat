@echo off
chcp 65001 >nul
REM 一键构建 Neko Custom Discs 支持的全部版本（Windows）
setlocal enabledelayedexpansion

set "ROOT=%~dp0.."
set "ENV=%ROOT%\.buildenv"
set "GRADLE_USER_HOME=%TEMP%\ghome"

REM 优先使用随项目附带的 JDK 21 + Gradle 8.14（不会被临时目录清理）
if exist "%ENV%\jdk\jdk-21.0.13+9\bin\java.exe" (
  set "JAVA_HOME=%ENV%\jdk\jdk-21.0.13+9"
  set "PATH=%JAVA_HOME%\bin;%PATH%"
) else (
  where java >nul 2>&1
  if errorlevel 1 (
    echo [错误] 未检测到 Java，请先安装 JDK 21 并配置 JAVA_HOME。
    echo 说明：这是开发者本机构建用的，玩家装模组时启动器会自动下载 Java。
    pause
    exit /b 1
  )
)

set VERSIONS=1.20.1 1.20.2 1.20.3 1.20.4 1.20.5 1.20.6 1.21 1.21.1 1.21.2 1.21.3 1.21.4 1.21.5 1.21.6 1.21.7 1.21.8 1.21.9 1.21.10 1.21.11
set OK=0
set FAIL=0

for %%%%v in (%%VERSIONS%%) do (
  echo ============================================
  echo  构建版本 %%%%v
  echo ============================================
  if exist "%ENV%\gradle-8.14\bin\gradle.bat" (
    call "%ENV%\gradle-8.14\bin\gradle.bat" build -Pmc=%%%%v --no-daemon --console=plain
  ) else (
    call "%ROOT%\gradlew.bat" build -Pmc=%%%%v --no-daemon --console=plain
  )
  if errorlevel 1 (
    set /a FAIL+=1
    echo [失败] %%%%v 构建失败，请看上方报错
  ) else (
    set /a OK+=1
    echo [成功] %%%%v
  )
)

echo.
echo ========== 构建汇总：成功 !OK! 个，失败 !FAIL! 个 ==========
echo 实际产物：
dir /b build\libs\customdiscs-*.jar 2>nul
if !FAIL! GTR 0 (
  echo.
  echo [未全部完成] 有 !FAIL! 个版本失败，请检查上方日志。
) else (
  echo.
  echo 全部完成，产物在 build\libs\ 目录。
)
endlocal
pause
