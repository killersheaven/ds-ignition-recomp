# Compiles DSIRecomp.cs into "DSI Recomp.exe" with the .NET Framework C# compiler included in Windows.
param([Parameter(Mandatory = $true)][string]$OutFile)
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) { $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe" }
if (-not (Test-Path $csc)) { Write-Warning "csc.exe (.NET Framework 4) not found; skipping DSI Recomp.exe - use Launcher.bat"; return }
$icon = Join-Path $here "..\..\branding\dsi.ico"
& $csc /nologo /target:winexe /optimize+ "/out:$OutFile" "/win32icon:$icon" /r:System.Windows.Forms.dll (Join-Path $here "DSIRecomp.cs")
if ($LASTEXITCODE -ne 0) { throw "csc failed with exit code $LASTEXITCODE" }
Write-Host "[launcher] built $OutFile"
