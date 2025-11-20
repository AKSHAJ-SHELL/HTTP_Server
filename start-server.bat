@echo off
REM Image Server Startup Script (Batch File)
REM This script ensures Docker containers are running on system startup

cd /d "%~dp0"

echo Starting Image Server...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Docker daemon is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo Warning: Docker daemon is not running. Please start Docker Desktop.
    echo Attempting to start Docker Desktop...
    
    REM Try to start Docker Desktop (if installed in default location)
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
        echo Waiting for Docker Desktop to start (30 seconds)...
        timeout /t 30 /nobreak >nul
        
        REM Check again
        docker ps >nul 2>&1
        if errorlevel 1 (
            echo Error: Docker Desktop did not start in time. Please start it manually.
            pause
            exit /b 1
        )
    ) else (
        echo Error: Docker Desktop not found. Please start Docker Desktop manually.
        pause
        exit /b 1
    )
)

REM Start the containers
echo Starting Docker containers...
docker-compose up -d
if errorlevel 1 (
    echo Error: Failed to start containers
    pause
    exit /b 1
)

echo.
echo Image Server started successfully!
echo Server is available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Container Status:
docker-compose ps

pause

