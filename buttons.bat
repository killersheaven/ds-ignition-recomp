@echo off
rem Switch Dead Space Ignition's on-screen button prompts.
rem   buttons.bat xbox      - original Xbox 360 buttons
rem   buttons.bat ps3       - PlayStation 3 buttons (from your PS3 copy)
rem   buttons.bat keyboard  - keyboard keys (matches the keys set in play.bat)
setlocal
set "ROOT=%~dp0"
set "DST=%ROOT%extracted\Resource\SumoTool"
if /i "%~1"=="xbox"     set "SRC=%ROOT%mods\original"
if /i "%~1"=="ps3"      set "SRC=%ROOT%mods\ps3_buttons"
if /i "%~1"=="keyboard" set "SRC=%ROOT%mods\keyboard_buttons"
if not defined SRC (
  echo Usage: buttons.bat xbox ^| ps3 ^| keyboard
  exit /b 1
)
set "RES=%ROOT%extracted\Resource"
for %%F in (subtitles_proj_EN.stz popups_EN.stz Frontend_EN.stz) do (
  if not exist "%SRC%\%%F" ( echo Missing %SRC%\%%F & exit /b 1 )
  copy /y "%SRC%\%%F" "%DST%\%%F" >nul || ( echo Could not copy %%F - is the game still running? & exit /b 1 )
)
for %%F in (HardwareCrack\HardwareCrackSet.zif HardwareCrack\HardwareCrackSet.zig SoftwareHack\SoftwareHackSet.zif SoftwareHack\SoftwareHackSet.zig) do (
  if not exist "%SRC%\%%F" ( echo Missing %SRC%\%%F & exit /b 1 )
  copy /y "%SRC%\%%F" "%RES%\%%F" >nul || ( echo Could not copy %%F - is the game still running? & exit /b 1 )
)
echo Button prompts set to %~1. Restart the game to see them.
