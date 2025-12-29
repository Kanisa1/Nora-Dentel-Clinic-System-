@echo off
REM =================================================================
REM Nora Dental Clinic - Manual Start Script
REM =================================================================
REM Use this to run the server manually (not as a service)

cd /d %~dp0

echo.
echo ============================================================
echo Starting Nora Dental Clinic System
echo ============================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Collect static files (if needed)
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Starting Django development server...
echo.
echo The clinic system will be available at:
echo   - http://localhost:8000
echo   - http://127.0.0.1:8000
echo.
echo Press CTRL+C to stop the server
echo.

REM Start the server
python manage.py runserver 0.0.0.0:8000

pause
