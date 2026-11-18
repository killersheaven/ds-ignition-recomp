@echo off
rem Starts DSI Recomp directly. Uses the "I own the full game" and language choices saved by Launcher.bat.
set "UNLOCK="
if exist "%~dp0launcher_settings.json" findstr /i /c:"true" "%~dp0launcher_settings.json" >nul && set "UNLOCK=--license_mask=1"
rem game language chosen in the launcher (1 English, 3 German, 4 French, 5 Spanish, 6 Italian)
set "LANGID=1"
if exist "%~dp0launcher_settings.json" for /f "tokens=2 delims=:, " %%a in ('findstr /c:"user_language" "%~dp0launcher_settings.json"') do set "LANGID=%%a"
set "UNLOCK=%UNLOCK% --user_language=%LANGID%"
if not exist "%~dp0bin\dsignition.exe" (
  call "%~dp0port\out\build\win-amd64-release\play.bat" %UNLOCK% %*
  goto :eof
)
if not exist "%~dp0extracted\default.xex" ( echo Game files not found. Run Setup first. & pause & goto :eof )
if not exist "%~dp0docs" mkdir "%~dp0docs"
cd /d "%~dp0bin"
dsignition.exe --game_data_root="%~dp0extracted" --gpu_plugin=xenos --mnk_mode=true --log_file="%~dp0docs\run_windows.log" %UNLOCK% %*
