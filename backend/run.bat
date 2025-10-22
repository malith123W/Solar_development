@echo off
echo Starting Electrical Data Analyzer Backend API...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting the backend API server...
echo Backend API will be available at: http://localhost:5000
echo API Documentation: http://localhost:5000/api/health
echo.
echo Press Ctrl+C to stop the backend server
echo.
python app.py
pause
