@echo off
REM =================================================================
REM Nora Dental Clinic - Service Uninstaller
REM =================================================================

echo.
echo ============================================================
echo Nora Dental Clinic - Service Uninstaller
echo ============================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ERROR: This script must be run as Administrator!
    pause
    exit /b 1
)

set SERVICE_NAME=NoraDentalClinic

REM Check if NSSM is available
where nssm >nul 2>&1
if %errorLevel% NEQ 0 (
    if not exist "nssm.exe" (
        echo ERROR: NSSM not found!
        pause
        exit /b 1
    )
    set NSSM=nssm.exe
) else (
    set NSSM=nssm
)

echo Stopping %SERVICE_NAME%...
%NSSM% stop %SERVICE_NAME%
timeout /t 3 /nobreak >nul

echo Removing %SERVICE_NAME%...
%NSSM% remove %SERVICE_NAME% confirm

echo.
echo Service removed successfully!
echo.
pause
