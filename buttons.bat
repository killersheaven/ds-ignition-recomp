@echo off
rem Switch Dead Space Ignition's on-screen button prompts.
rem   buttons.bat xbox      - original Xbox 360 buttons
rem   buttons.bat ps3       - PlayStation buttons
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
rem menu, subtitle and pop-up prompts: one copy per game language (English is required)
if not exist "%SRC%\Frontend_EN.stz" ( echo Missing %SRC%\Frontend_EN.stz - run Setup first & exit /b 1 )
for %%L in (EN FR GE IT SP) do for %%N in (subtitles_proj popups Frontend) do (
  if exist "%SRC%\%%N_%%L.stz" copy /y "%SRC%\%%N_%%L.stz" "%DST%\%%N_%%L.stz" >nul || ( echo Could not copy %%N_%%L.stz - is the game still running? & exit /b 1 )
)
for %%F in (HardwareCrack\HardwareCrackSet.zif HardwareCrack\HardwareCrackSet.zig SoftwareHack\SoftwareHackSet.zif SoftwareHack\SoftwareHackSet.zig) do (
  if not exist "%SRC%\%%F" ( echo Missing %SRC%\%%F & exit /b 1 )
  copy /y "%SRC%\%%F" "%RES%\%%F" >nul || ( echo Could not copy %%F - is the game still running? & exit /b 1 )
)
echo Button prompts set to %~1. Restart the game to see them.
