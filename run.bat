@echo off
echo Starting Electrical Data Analyzer...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting the application...
echo Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.
python app.py
pause
