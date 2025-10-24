@echo off
REM Script to prepare repositories for separate Vercel deployment
REM Run this script from the root of your Solar_development project

echo 🚀 Preparing Solar Development for separate Vercel deployment...

REM Create backend repository structure
echo 📁 Creating backend repository structure...
if not exist "..\solar-development-backend" mkdir "..\solar-development-backend"
xcopy "backend\*" "..\solar-development-backend\" /E /I /Y
echo ✅ Backend files copied to ..\solar-development-backend\

REM Create frontend repository structure
echo 📁 Creating frontend repository structure...
if not exist "..\solar-development-frontend" mkdir "..\solar-development-frontend"
xcopy "frontend\*" "..\solar-development-frontend\" /E /I /Y
echo ✅ Frontend files copied to ..\solar-development-frontend\

echo.
echo 🎉 Setup complete!
echo.
echo Next steps:
echo 1. Initialize git repositories in both folders:
echo    cd ..\solar-development-backend ^&^& git init ^&^& git add . ^&^& git commit -m "Initial backend commit"
echo    cd ..\solar-development-frontend ^&^& git init ^&^& git add . ^&^& git commit -m "Initial frontend commit"
echo.
echo 2. Create repositories on GitHub/GitLab/Bitbucket
echo.
echo 3. Push code to repositories
echo.
echo 4. Follow the deployment instructions in DEPLOYMENT_INSTRUCTIONS.md
echo.
echo 📁 Backend files: ..\solar-development-backend\
echo 📁 Frontend files: ..\solar-development-frontend\
pause
