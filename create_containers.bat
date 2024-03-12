@echo off

REM Set the base image name
set imageName=steam2buff

REM Build the Docker image
docker build -t %imageName% .

REM Loop to create 100 containers
for /L %%i in (1,1,100) do (
    set containerName=steam2buff-%%i
    docker run --name=%containerName% --restart=always -d %imageName%
    
    REM Add a delay of 10 seconds
    timeout /nobreak /t 10 >nul
)