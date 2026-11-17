@echo off
rem Starts DSI Recomp directly. Uses the "I own the full game" choice saved by Launcher.bat.
set "UNLOCK="
if exist "%~dp0launcher_settings.json" findstr /i /c:"true" "%~dp0launcher_settings.json" >nul && set "UNLOCK=--license_mask=1"
if not exist "%~dp0bin\dsignition.exe" (
  call "%~dp0port\out\build\win-amd64-release\play.bat" %UNLOCK% %*
  goto :eof
)
if not exist "%~dp0extracted\default.xex" ( echo Game files not found. Run Setup first. & pause & goto :eof )
if not exist "%~dp0docs" mkdir "%~dp0docs"
cd /d "%~dp0bin"
dsignition.exe --game_data_root="%~dp0extracted" --gpu_plugin=xenos --mnk_mode=true --log_file="%~dp0docs\run_windows.log" %UNLOCK% %*
