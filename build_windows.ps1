# Dead Space Ignition - native PC build (ReXGlue)
#
# Run from ANY PowerShell window (it sets up the 64-bit Visual Studio environment itself):
#     cd D:\DSIgnitionport
#     powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
#
# First run: about 20-40 min. Later runs only rebuild what changed.
# Output: port\out\build\win-amd64-release\dsignition.exe (+ play.bat). Full log: docs\build_windows.log

$ErrorActionPreference = "Stop"
$root   = $PSScriptRoot
$sdk    = Join-Path $root "rexglue-sdk"
$sdkRev = "546a082"   # SDK commit the project was generated with (v0.10.0-dev, 2026-11-06)
$log    = Join-Path $root "docs\build_windows.log"
"Build started $(Get-Date)" | Set-Content $log -Encoding UTF8

function Log($msg) { Write-Host $msg -ForegroundColor Cyan; $msg | Add-Content $log -Encoding UTF8 }
# Run a native command, show + log all of its output, stop on failure.
function Run {
    param([Parameter(ValueFromRemainingArguments)]$cmd)
    $exe, $rest = $cmd
    Log ">> $($cmd -join ' ')"
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & $exe @rest 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append | Write-Host
    $code = $LASTEXITCODE; $ErrorActionPreference = $prev
    if ($code -ne 0) { Log "FAILED (exit $code): $($cmd -join ' ')"; throw "Build step failed - see docs\build_windows.log" }
}

# 1. 64-bit Visual Studio developer environment (fixes 'undefined symbol: mainCRTStartup' from a 32-bit shell)
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw "Visual Studio with the C++ tools was not found." }
Import-Module (Join-Path $vs "Common7\Tools\Microsoft.VisualStudio.DevShell.dll")
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments "-arch=x64 -host_arch=x64" | Out-Null
Log "VS environment: $vs (x64). LIB=$($env:LIB.Split(';')[0])"

# 2. Toolchain: newest clang first; drop MinGW (WinLibs) tools from PATH
$llvm = @("C:\Program Files\LLVM\bin", "$vs\VC\Tools\Llvm\x64\bin") |
        Where-Object { Test-Path (Join-Path $_ "clang++.exe") } |
        Sort-Object { [int]((& (Join-Path $_ "clang++.exe") --version | Select-Object -First 1) -replace '.*version (\d+)\..*','$1') } -Descending |
        Select-Object -First 1
if (-not $llvm) { throw "clang++ not found. Run: winget install LLVM.LLVM" }
$env:PATH = "$llvm;" + (($env:PATH -split ';' | Where-Object { $_ -and $_ -notmatch 'WinLibs|mingw' }) -join ';')
$clangLine = & clang++ --version | Select-Object -First 1
Log "Compiler: $clangLine ($llvm)"
Log "CMake: $(& cmake --version | Select-Object -First 1)   Ninja: $(& ninja --version)"
if ([int]($clangLine -replace '.*version (\d+)\..*','$1') -lt 20) { throw "ReXGlue needs clang 20+. Run: winget install LLVM.LLVM" }

# 3. ReXGlue SDK: clone (pinned), configure, build, install
if (-not (Test-Path (Join-Path $sdk ".git"))) {
    Run git clone --recursive https://github.com/rexglue/rexglue-sdk.git $sdk
}
Push-Location $sdk
Run git checkout $sdkRev
Run git submodule update --init --recursive
# Clear a configure cache left by a failed run (e.g. the earlier 32-bit attempt)
if ((Test-Path "out\build\win-amd64\CMakeCache.txt") -and -not (Test-Path "out\install\win-amd64")) { Remove-Item -Recurse -Force "out\build\win-amd64" }
Run cmake --preset win-amd64
Run cmake --build out/build/win-amd64 --config Release --target install
Pop-Location
$install = Join-Path $sdk "out\install\win-amd64"

# 4. The game project (codegen runs as part of the build)
Push-Location (Join-Path $root "port")
$exeDir = Join-Path $root "port\out\build\win-amd64-release"
if ((Test-Path "$exeDir\CMakeCache.txt") -and -not (Test-Path "$exeDir\dsignition.exe")) { Remove-Item -Recurse -Force $exeDir }
$env:CMAKE_PREFIX_PATH = $install
Run cmake --preset win-amd64-release
Run cmake --build --preset win-amd64-release
Pop-Location
if (-not (Test-Path "$exeDir\dsignition.exe")) { throw "Build finished but dsignition.exe is missing - see docs\build_windows.log" }

# 5. Runtime DLLs (incl. GPU plugin rexgpu-xenos.dll) next to the exe, plus a launcher
Get-ChildItem (Join-Path $install "bin"), (Join-Path $install "lib") -Filter *.dll -ErrorAction SilentlyContinue |
    Copy-Item -Destination $exeDir -Force
# Killers' Heaven boot splash logo (loaded from branding\ next to the exe; no file = no splash)
New-Item -ItemType Directory -Force (Join-Path $exeDir "branding") | Out-Null
Copy-Item (Join-Path $root "branding\killers_heaven_on_dark.png") (Join-Path $exeDir "branding") -Force -ErrorAction SilentlyContinue
@"
@echo off
cd /d "%~dp0"
dsignition.exe --game_data_root="$root\extracted" --gpu_plugin=xenos --mnk_mode=true --log_file="$root\docs\run_windows.log" %*
"@ | Set-Content -Path (Join-Path $exeDir "play.bat") -Encoding ASCII

Log "DONE. Start the game with:  $exeDir\play.bat"
