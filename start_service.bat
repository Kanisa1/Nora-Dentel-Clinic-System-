@echo off
REM Nora Dental Clinic - Start Script for NSSM Service
REM This script starts the Django application using waitress-serve

cd /d %~dp0
call venv\Scripts\activate.bat

REM Start with waitress (production-ready WSGI server for Windows)
waitress-serve --host=0.0.0.0 --port=8000 --threads=4 config.wsgi:application
