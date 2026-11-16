@echo off
rem Opens the launcher: pick button prompts (Xbox / PS3 / Keyboard), then Play.
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0tools\launcher\launcher.ps1"
