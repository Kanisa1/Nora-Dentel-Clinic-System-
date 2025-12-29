@echo off
REM =================================================================
REM Nora Dental Clinic - NSSM Service Installation Script
REM =================================================================
REM This script installs the Django app as a Windows Service using NSSM
REM Download NSSM from: https://nssm.cc/download

echo.
echo ============================================================
echo Nora Dental Clinic - Windows Service Installer
echo ============================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: This script must be run as Administrator!
    echo Right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Set variables
set SERVICE_NAME=NoraDentalClinic
set APP_DIR=%~dp0
set PYTHON_EXE=%APP_DIR%venv\Scripts\python.exe
set MANAGE_PY=%APP_DIR%manage.py
set START_SCRIPT=%APP_DIR%start_service.bat

echo Current directory: %APP_DIR%
echo Python executable: %PYTHON_EXE%
echo.

REM Check if NSSM is in PATH or current directory
where nssm >nul 2>&1
if %errorLevel% NEQ 0 (
    if not exist "nssm.exe" (
        echo ERROR: NSSM not found!
        echo.
        echo Please download NSSM from: https://nssm.cc/download
        echo Extract nssm.exe to this folder or add it to your PATH
        pause
        exit /b 1
    )
    set NSSM=nssm.exe
) else (
    set NSSM=nssm
)

echo Using NSSM: %NSSM%
echo.

REM Check if service already exists
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% EQU 0 (
    echo Service %SERVICE_NAME% already exists!
    echo Stopping and removing existing service...
    %NSSM% stop %SERVICE_NAME%
    timeout /t 2 /nobreak >nul
    %NSSM% remove %SERVICE_NAME% confirm
    timeout /t 2 /nobreak >nul
)

REM Install the service
echo.
echo Installing %SERVICE_NAME% service...
%NSSM% install %SERVICE_NAME% "%PYTHON_EXE%" "%MANAGE_PY%" runserver 0.0.0.0:8000 --noreload

REM Configure service
echo Configuring service...
%NSSM% set %SERVICE_NAME% AppDirectory "%APP_DIR%"
%NSSM% set %SERVICE_NAME% DisplayName "Nora Dental Clinic System"
%NSSM% set %SERVICE_NAME% Description "Healthcare Management System for Nora Dental Clinic"
%NSSM% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM% set %SERVICE_NAME% AppStdout "%APP_DIR%logs\service.log"
%NSSM% set %SERVICE_NAME% AppStderr "%APP_DIR%logs\service_error.log"
%NSSM% set %SERVICE_NAME% AppRotateFiles 1
%NSSM% set %SERVICE_NAME% AppRotateOnline 1
%NSSM% set %SERVICE_NAME% AppRotateBytes 10485760

REM Create logs directory
if not exist "%APP_DIR%logs" mkdir "%APP_DIR%logs"

REM Start the service
echo.
echo Starting %SERVICE_NAME% service...
%NSSM% start %SERVICE_NAME%

echo.
echo ============================================================
echo Service installed successfully!
echo ============================================================
echo.
echo Service Name: %SERVICE_NAME%
echo Display Name: Nora Dental Clinic System
echo Status: Starting...
echo.
echo To check service status: nssm status %SERVICE_NAME%
echo To stop service: nssm stop %SERVICE_NAME%
echo To restart service: nssm restart %SERVICE_NAME%
echo To remove service: nssm remove %SERVICE_NAME%
echo.
echo Logs location: %APP_DIR%logs\
echo.
echo The clinic system will be available at:
echo   - http://localhost:8000
echo   - http://[SERVER-IP]:8000
echo.
echo IMPORTANT: Make sure to:
echo   1. Configure Windows Firewall to allow port 8000
echo   2. Update .env file with production settings
echo   3. Run: python manage.py collectstatic
echo.
pause
