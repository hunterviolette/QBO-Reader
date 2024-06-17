@echo off
docker info >nul 2>&1
if %errorlevel% neq 0 (
  echo Docker daemon is not running. Starting Docker...
  start docker
)

if %errorlevel% neq 0 (
  echo Failed to start docker, please start docker manually
)

git pull
docker-compose up --build
echo turning off container
pause