@echo off
rem Starts DSI Recomp directly. Uses the "I own the full game" choice saved by Launcher.bat.
set "UNLOCK="
if exist "%~dp0launcher_settings.json" findstr /i /c:"true" "%~dp0launcher_settings.json" >nul && set "UNLOCK=--license_mask=1"
call "%~dp0port\out\build\win-amd64-release\play.bat" %UNLOCK% %*
