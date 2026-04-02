@echo off
setlocal

set "ROLE=%~1"
if "%ROLE%"=="" set "ROLE=all"

set "COLLECTION=postman\finance-dashboard-role-tests.postman_collection.json"
set "ENVIRONMENT=postman\finance-dashboard-local.postman_environment.json"

cd /d "%~dp0\.."

if /i "%ROLE%"=="admin" goto RUN_ADMIN
if /i "%ROLE%"=="analyst" goto RUN_ANALYST
if /i "%ROLE%"=="viewer" goto RUN_VIEWER
if /i "%ROLE%"=="all" goto RUN_ALL

echo Invalid role: %ROLE%
echo Usage: scripts\newman-role-tests.bat [admin^|analyst^|viewer^|all]
exit /b 1

:RUN_ADMIN
echo Running Newman folder: Role - Admin
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Admin" --reporters cli
exit /b %ERRORLEVEL%

:RUN_ANALYST
echo Running Newman folder: Role - Analyst
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Analyst" --reporters cli
exit /b %ERRORLEVEL%

:RUN_VIEWER
echo Running Newman folder: Role - Viewer
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Viewer" --reporters cli
exit /b %ERRORLEVEL%

:RUN_ALL
echo Running Newman folder: Role - Admin
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Admin" --reporters cli
if errorlevel 1 exit /b %ERRORLEVEL%

echo Running Newman folder: Role - Analyst
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Analyst" --reporters cli
if errorlevel 1 exit /b %ERRORLEVEL%

echo Running Newman folder: Role - Viewer
npx newman run "%COLLECTION%" -e "%ENVIRONMENT%" --folder "Role - Viewer" --reporters cli
exit /b %ERRORLEVEL%
