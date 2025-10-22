@echo off
echo Starting Electrical Data Analyzer - Full Stack Application
echo =========================================================
echo.
echo This will start both the backend API and frontend React app
echo.
echo Backend API: http://localhost:5000
echo Frontend App: http://localhost:3000
echo.
echo Press any key to continue...
pause
echo.

echo Starting Backend API Server...
start "Backend API" cmd /k "cd backend && python app.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak > nul

echo Starting Frontend React App...
start "Frontend App" cmd /k "cd frontend && npm start"

echo.
echo Both servers are starting up...
echo Backend API: http://localhost:5000
echo Frontend App: http://localhost:3000
echo.
echo The applications will open in separate windows.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this launcher...
pause
